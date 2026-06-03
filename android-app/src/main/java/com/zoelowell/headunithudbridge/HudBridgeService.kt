package com.zoelowell.headunithudbridge

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import android.util.Log
import java.time.Clock
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class HudBridgeService : Service(), Esp32DiscoveryClient.Listener {
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()
    private val retryHandler = Handler(Looper.getMainLooper())
    private val hudState = HudBridgeState()
    private val speedState = HudSpeedState()
    private val navigationFreshnessGate = NavigationFreshnessGate()
    private val clock: Clock = Clock.systemDefaultZone()
    private val discoveryBackoff = RetryBackoff(
        initialDelayMillis = DISCOVERY_RETRY_INITIAL_MS,
        maxDelayMillis = DISCOVERY_RETRY_MAX_MS
    )
    private var locationManager: LocationManager? = null
    private var speedTrackingStarted = false
    private var discoveryClient: Esp32DiscoveryClient? = null
    private var discoveryInFlight = false
    private var discoveryRetryScheduled = false
    private var espConnectionState = EspConnectionObservedState.DISCONNECTED
    private var nextEspDiscoveryRetryAtMillis = 0L

    private val speedReplayTicker = object : Runnable {
        override fun run() {
            executor.execute {
                sendPayload(speedState.currentPacket().toJson())
            }
            retryHandler.postDelayed(this, SPEED_REPLAY_INTERVAL_MS)
        }
    }

    private val locationListener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            val packet = if (location.hasSpeed()) {
                HudSpeedPacket.fromMetersPerSecond(location.speed)
            } else {
                HudSpeedPacket.unknown()
            }
            executor.execute {
                speedState.update(packet)
            }
        }

        @Deprecated("Deprecated in Android API")
        override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) = Unit

        override fun onProviderEnabled(provider: String) = Unit

        override fun onProviderDisabled(provider: String) {
            executor.execute {
                speedState.update(HudSpeedPacket.unknown())
            }
        }
    }

    private val headunitReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                HeadunitRevivedBroadcast.ACTION_NAVIGATION_UPDATE -> {
                    if (!navigationFreshnessGate.shouldAccept(intent.toNavigationFreshnessSample())) {
                        return
                    }
                    val packet = intent.toHudNavigationPacket().withRenderedHudBitmaps()
                    executor.execute {
                        val navigationSent = sendPayload(hudState.onNavigationPacket(packet))
                        val speedSent = sendPayload(speedState.currentPacket().toJson())
                        requestEsp32DiscoveryAfterHudSend()
                        publishBridgeStatus(if (navigationSent || speedSent) LAST_EVENT_NAVIGATION_SENT else LAST_EVENT_NAVIGATION_FAILED)
                    }
                }
                HeadunitRevivedBroadcast.ACTION_PROJECTION_REQUEST -> {
                    executor.execute {
                        val sent = sendPayload(hudState.onProjectionRequest())
                        requestEsp32DiscoveryAfterHudSend()
                        publishBridgeStatus(if (sent) LAST_EVENT_PROJECTION_SENT else LAST_EVENT_PROJECTION_FAILED)
                    }
                }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        startForegroundNotification(includeLocation = false)
        registerHeadunitReceiver()
        startSpeedTrackingIfPermitted()
        executor.execute {
            if (hasKnownTarget()) {
                sendCurrentSettingsIfTargetAccepts()
            }
            publishBridgeStatus(LAST_EVENT_SERVICE_STARTED)
        }
        retryHandler.post(speedReplayTicker)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START_SPEED_TRACKING -> {
                startSpeedTrackingIfPermitted()
            }
            ACTION_REFRESH_STATE -> {
                executor.execute {
                    val payload = hudState.payloadForRefresh()
                    if (payload == null) {
                        publishBridgeStatus(LAST_EVENT_REFRESH_NO_STATE)
                    } else {
                        val sent = sendPayload(payload)
                        publishBridgeStatus(if (sent) LAST_EVENT_REFRESH_SENT else LAST_EVENT_REFRESH_FAILED)
                    }
                }
            }
            ACTION_PUBLISH_STATUS -> {
                executor.execute {
                    publishBridgeStatus(LAST_EVENT_STATUS_REQUEST)
                }
            }
            ACTION_DISCOVER_ESP32 -> {
                executor.execute {
                    requestEsp32Discovery()
                }
            }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        retryHandler.removeCallbacksAndMessages(null)
        discoveryClient?.close()
        discoveryClient = null
        unregisterReceiver(headunitReceiver)
        stopSpeedTracking()
        executor.execute {
            sendPayload(HudNavigationPacket.inactive().toHudJson())
        }
        executor.shutdown()
        try {
            if (!executor.awaitTermination(500L, TimeUnit.MILLISECONDS)) {
                executor.shutdownNow()
            }
        } catch (e: InterruptedException) {
            executor.shutdownNow()
            Thread.currentThread().interrupt()
        }
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun registerHeadunitReceiver() {
        val filter = IntentFilter().apply {
            addAction(HeadunitRevivedBroadcast.ACTION_NAVIGATION_UPDATE)
            addAction(HeadunitRevivedBroadcast.ACTION_PROJECTION_REQUEST)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(headunitReceiver, filter, Context.RECEIVER_EXPORTED)
        } else {
            registerReceiver(headunitReceiver, filter)
        }
    }

    private fun startSpeedTrackingIfPermitted() {
        if (speedTrackingStarted) {
            return
        }
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return
        }

        val manager = getSystemService(LocationManager::class.java) ?: return
        locationManager = manager

        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
            .filter { provider -> runCatching { manager.isProviderEnabled(provider) }.getOrDefault(false) }
        if (providers.isEmpty()) {
            return
        }

        startForegroundNotification(includeLocation = true)
        providers.forEach { provider ->
            @Suppress("MissingPermission")
            manager.requestLocationUpdates(
                provider,
                SPEED_UPDATE_INTERVAL_MS,
                SPEED_UPDATE_DISTANCE_METERS,
                locationListener,
                Looper.getMainLooper()
            )
            @Suppress("MissingPermission")
            manager.getLastKnownLocation(provider)?.let(locationListener::onLocationChanged)
        }
        speedTrackingStarted = true
    }

    private fun startForegroundNotification(includeLocation: Boolean) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            var serviceType = ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            if (includeLocation) {
                serviceType = serviceType or ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION
            }
            startForeground(NOTIFICATION_ID, createNotification(), serviceType)
        } else {
            startForeground(NOTIFICATION_ID, createNotification())
        }
    }

    private fun stopSpeedTracking() {
        if (!speedTrackingStarted) {
            return
        }
        locationManager?.removeUpdates(locationListener)
        speedTrackingStarted = false
    }

    private fun sendPayload(payload: String): Boolean {
        val savedTargetHost = ProvisioningStore.targetHost(this@HudBridgeService)
        val targetHost = savedTargetHost ?: DEFAULT_TARGET_HOST
        val targetPort = ProvisioningStore.targetPort(this@HudBridgeService)
        val sequencedPayload = HudUdpPayloadSequencer.wrap(payload, SystemClock.elapsedRealtime())
        var sent = false
        var failed = false
        HudUdpTargetPlan.forTarget(targetHost, targetPort).forEach { target ->
            val result = UdpHudSender(target.host, target.port).sendFireAndForget(sequencedPayload)
            if (result.errorMessage != null) {
                failed = true
                Log.w(TAG, "HUD UDP send failed to ${target.host}:${target.port}: ${result.errorMessage}")
            } else {
                sent = true
                Log.d(TAG, "HUD UDP sent to ${target.host}:${target.port}")
            }
        }
        val nextEspConnectionState = when {
            !savedTargetHost.isNullOrBlank() && sent && !failed -> EspConnectionObservedState.CONNECTED
            discoveryInFlight -> EspConnectionObservedState.DISCOVERING
            discoveryRetryScheduled -> EspConnectionObservedState.RETRY_WAITING
            else -> EspConnectionObservedState.DISCONNECTED
        }
        updateEspConnectionState(nextEspConnectionState)
        return sent
    }

    private fun updateEspConnectionState(nextState: EspConnectionObservedState) {
        if (espConnectionState == nextState) {
            return
        }

        espConnectionState = nextState
        when (nextState) {
            EspConnectionObservedState.CONNECTED -> publishBridgeStatus(LAST_EVENT_ESP_CONNECTED)
            EspConnectionObservedState.DISCONNECTED -> publishBridgeStatus(LAST_EVENT_ESP_DISCONNECTED)
            EspConnectionObservedState.DISCOVERING,
            EspConnectionObservedState.RETRY_WAITING -> Unit
        }
    }

    private fun requestEsp32DiscoveryAfterHudSend() {
        if (Esp32DiscoveryPolicy.shouldStartAfterHudSend(hasKnownTarget = hasKnownTarget())) {
            requestEsp32Discovery()
        }
    }

    private fun hasKnownTarget(): Boolean {
        return !ProvisioningStore.targetHost(this@HudBridgeService).isNullOrBlank()
    }

    private fun requestEsp32Discovery() {
        if (discoveryInFlight) {
            return
        }
        if (espConnectionState == EspConnectionObservedState.CONNECTED) {
            return
        }

        discoveryClient?.close()
        discoveryClient = Esp32DiscoveryClient(applicationContext, this)
        discoveryInFlight = true
        espConnectionState = EspConnectionObservedState.DISCOVERING
        nextEspDiscoveryRetryAtMillis = 0L
        discoveryClient?.start(SERVICE_DISCOVERY_TIMEOUT_MS)
        publishBridgeStatus(LAST_EVENT_DISCOVERY_STARTED)
    }

    private fun scheduleEsp32DiscoveryRetry(): Boolean {
        if (discoveryRetryScheduled || !shouldRetryEsp32Discovery()) {
            return false
        }

        val delayMillis = discoveryBackoff.nextDelayMillis()
        discoveryRetryScheduled = true
        nextEspDiscoveryRetryAtMillis = clock.millis() + delayMillis
        espConnectionState = EspConnectionObservedState.RETRY_WAITING
        retryHandler.postDelayed(
            {
                discoveryRetryScheduled = false
                nextEspDiscoveryRetryAtMillis = 0L
                executor.execute {
                    requestEsp32Discovery()
                }
            },
            delayMillis
        )
        return true
    }

    private fun shouldRetryEsp32Discovery(): Boolean {
        return Esp32DiscoveryPolicy.shouldRetry(
            headunitState = hudState.statusSnapshot().headunitState,
            espConnectionState = espConnectionState
        )
    }

    override fun onDiscoveryMessage(message: String) {
        Log.d(TAG, message)
    }

    override fun onEsp32Discovered(host: String, port: Int, targetKind: HudTargetKind) {
        ProvisioningStore.saveTarget(this, host, port, targetKind)
        discoveryInFlight = false
        discoveryRetryScheduled = false
        nextEspDiscoveryRetryAtMillis = 0L
        discoveryBackoff.reset()

        executor.execute {
            val settingsAck = sendCurrentSettingsIfTargetAccepts()
            val replaySent = hudState.payloadForRefresh()?.let(::sendPayload) ?: false
            val targetReady = !targetKind.receivesEsp32Settings
            publishBridgeStatus(if (targetReady || settingsAck || replaySent) LAST_EVENT_DISCOVERY_FOUND_SENT else LAST_EVENT_DISCOVERY_FOUND_FAILED)
        }
    }

    private fun sendCurrentSettingsIfTargetAccepts(): Boolean {
        return if (ProvisioningStore.targetKind(this).receivesEsp32Settings) {
            sendCurrentSettings()
        } else {
            false
        }
    }

    private fun sendCurrentSettings(): Boolean {
        return sendPayload(
            Esp32SettingsPacket(
                debugOverlay = ProvisioningStore.debugOverlayEnabled(this),
                speedUnitVisible = ProvisioningStore.speedUnitVisible(this),
                speedFontSize = ProvisioningStore.speedFontSize(this),
                hudLanguage = ProvisioningStore.hudLanguage(this)
            ).toJson()
        )
    }

    override fun onEsp32DiscoveryFailed(message: String) {
        Log.w(TAG, message)
        discoveryInFlight = false
        if (espConnectionState == EspConnectionObservedState.CONNECTED) {
            return
        }
        executor.execute {
            if (!scheduleEsp32DiscoveryRetry()) {
                espConnectionState = EspConnectionObservedState.DISCONNECTED
                nextEspDiscoveryRetryAtMillis = 0L
            }
            publishBridgeStatus(LAST_EVENT_DISCOVERY_FAILED)
        }
    }

    private fun publishBridgeStatus(lastEvent: String) {
        val snapshot = hudState.statusSnapshot()
        val speedPacket = speedState.currentPacket()
        val intent = Intent(HudBridgeStatusBroadcast.ACTION_BRIDGE_STATUS).apply {
            setPackage(packageName)
            putExtra(HudBridgeStatusBroadcast.EXTRA_HEADUNIT_STATE, snapshot.headunitState.name)
            putExtra(HudBridgeStatusBroadcast.EXTRA_HUD_OUTPUT_STATE, snapshot.hudOutputState.name)
            putExtra(HudBridgeStatusBroadcast.EXTRA_ESP_CONNECTION_STATE, espConnectionState.name)
            putExtra(HudBridgeStatusBroadcast.EXTRA_LAST_EVENT, lastEvent)
            putExtra(HudBridgeStatusBroadcast.EXTRA_LAST_EVENT_TIME_MILLIS, clock.millis())
            putExtra(HudBridgeStatusBroadcast.EXTRA_SPEED_KMH, speedPacket.speedKmh)
            putExtra(
                HudBridgeStatusBroadcast.EXTRA_NEXT_ESP_DISCOVERY_RETRY_AT_MILLIS,
                nextEspDiscoveryRetryAtMillis
            )
        }
        sendBroadcast(intent)
    }

    private fun createNotification(): Notification {
        val localizedContext = this.withHudLocale()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java)
            val channel = NotificationChannel(
                CHANNEL_ID,
                localizedContext.getString(R.string.hud_bridge_notification_channel),
                NotificationManager.IMPORTANCE_LOW
            )
            manager.createNotificationChannel(channel)
        }

        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }

        return builder
            .setSmallIcon(android.R.drawable.ic_dialog_map)
            .setContentTitle(localizedContext.getString(R.string.hud_bridge_notification_title))
            .setContentText(localizedContext.getString(R.string.hud_bridge_notification_text))
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "hud_bridge"
        private const val TAG = "HudBridgeService"
        private const val NOTIFICATION_ID = 1001
        private const val DEFAULT_TARGET_HOST = HudUdpTargetPlan.BROADCAST_HOST
        private const val SPEED_UPDATE_INTERVAL_MS = 500L
        private const val SPEED_UPDATE_DISTANCE_METERS = 0f
        private const val SPEED_REPLAY_INTERVAL_MS = BridgeUpdateIntervals.SPEED_REPLAY_MILLIS
        private const val SERVICE_DISCOVERY_TIMEOUT_MS = 8_000L
        private const val DISCOVERY_RETRY_INITIAL_MS = 10_000L
        private const val DISCOVERY_RETRY_MAX_MS = 60_000L
        const val ACTION_START_SPEED_TRACKING = "com.zoelowell.headunithudbridge.ACTION_START_SPEED_TRACKING"
        const val ACTION_REFRESH_STATE = "com.zoelowell.headunithudbridge.ACTION_REFRESH_STATE"
        const val ACTION_PUBLISH_STATUS = "com.zoelowell.headunithudbridge.ACTION_PUBLISH_STATUS"
        const val ACTION_DISCOVER_ESP32 = "com.zoelowell.headunithudbridge.ACTION_DISCOVER_ESP32"

        private const val LAST_EVENT_SERVICE_STARTED = "service_started"
        private const val LAST_EVENT_STATUS_REQUEST = "status_request"
        private const val LAST_EVENT_REFRESH_NO_STATE = "refresh_no_headunit_state"
        private const val LAST_EVENT_REFRESH_SENT = "refresh_sent"
        private const val LAST_EVENT_REFRESH_FAILED = "refresh_failed"
        private const val LAST_EVENT_PROJECTION_SENT = "projection_sent"
        private const val LAST_EVENT_PROJECTION_FAILED = "projection_failed"
        private const val LAST_EVENT_NAVIGATION_SENT = "navigation_sent"
        private const val LAST_EVENT_NAVIGATION_FAILED = "navigation_failed"
        private const val LAST_EVENT_DISCOVERY_STARTED = "esp32_discovery_started"
        private const val LAST_EVENT_DISCOVERY_FOUND_SENT = "esp32_discovery_found_sent"
        private const val LAST_EVENT_DISCOVERY_FOUND_FAILED = "esp32_discovery_found_failed"
        private const val LAST_EVENT_DISCOVERY_FAILED = "esp32_discovery_failed"
        private const val LAST_EVENT_ESP_CONNECTED = "esp32_connected"
        private const val LAST_EVENT_ESP_DISCONNECTED = "esp32_disconnected"
    }
}
