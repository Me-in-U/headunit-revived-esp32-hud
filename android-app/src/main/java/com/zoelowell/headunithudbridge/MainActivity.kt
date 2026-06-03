package com.zoelowell.headunithudbridge

import android.Manifest
import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import android.provider.Settings
import android.text.Editable
import android.text.InputType
import android.text.TextWatcher
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.SeekBar
import android.widget.Switch
import android.widget.TableLayout
import android.widget.TableRow
import android.widget.TextView
import android.widget.Toast
import java.util.Locale
import java.util.concurrent.Executors

private data class RawNavigationField(
    val variable: String,
    val descriptionResId: Int
)

private data class NavigationBroadcastValue(
    val variable: String,
    val value: String
)

fun Context.withHudLocale(): Context {
    val configuration = Configuration(resources.configuration)
    configuration.setLocale(Locale.forLanguageTag(ProvisioningStore.hudLanguage(this)))
    return createConfigurationContext(configuration)
}

class MainActivity : Activity(), BleProvisioningClient.Listener, Esp32DiscoveryClient.Listener {
    private val networkExecutor = Executors.newSingleThreadExecutor()
    private val autoDiscoveryGate = AutoDiscoveryGate()
    private val navigationFreshnessGate = NavigationFreshnessGate()
    private val uiHandler = Handler(Looper.getMainLooper())

    private lateinit var ssidInput: EditText
    private lateinit var passwordInput: EditText
    private lateinit var wifiSummaryView: TextView
    private lateinit var wifiEditorContainer: LinearLayout
    private lateinit var wifiEditButton: Button
    private lateinit var espDiscoverButton: Button
    private lateinit var targetValueView: TextView
    private lateinit var headunitValueView: TextView
    private lateinit var espValueView: TextView
    private lateinit var hudValueView: TextView
    private lateinit var retryValueView: TextView
    private lateinit var eventValueView: TextView
    private lateinit var permissionAllowedView: TextView
    private lateinit var permissionDeniedView: TextView
    private lateinit var backgroundValueView: TextView
    private lateinit var permissionActionsRow: LinearLayout
    private lateinit var runtimePermissionButton: Button
    private lateinit var batteryOptimizationButton: Button
    private lateinit var rawNavigationTable: TableLayout
    private lateinit var statusView: TextView
    private lateinit var displaySimulatorView: HudDisplaySimulatorView
    private lateinit var debugSwitch: Switch
    private lateinit var speedUnitSwitch: Switch
    private lateinit var speedFontSizeValueView: TextView
    private val rawNavigationValueViews = mutableMapOf<String, TextView>()
    private var bleClient: BleProvisioningClient? = null
    private var discoveryClient: Esp32DiscoveryClient? = null
    private var androidAutoReceiverRegistered = false
    private var bridgeStatusReceiverRegistered = false
    private var wifiEditorVisible = false
    private var bridgeStatus = BridgeDashboardStatus(
        headunitState = HeadunitObservedState.WAITING_FOR_BROADCAST,
        hudOutputState = HudOutputState.NONE,
        espConnectionState = EspConnectionObservedState.DISCONNECTED,
        lastEvent = "",
        lastEventTimeMillis = 0L,
        nextEspDiscoveryRetryAtMillis = 0L
    )

    private val bridgeStatusTicker = object : Runnable {
        override fun run() {
            renderDashboardStatus()
            uiHandler.postDelayed(this, STATUS_TICK_INTERVAL_MS)
        }
    }

    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(newBase.withHudLocale())
    }

    private val bridgeStatusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action != HudBridgeStatusBroadcast.ACTION_BRIDGE_STATUS) {
                return
            }

            bridgeStatus = BridgeDashboardStatus(
                headunitState = parseHeadunitState(
                    intent.getStringExtra(HudBridgeStatusBroadcast.EXTRA_HEADUNIT_STATE)
                ),
                hudOutputState = parseHudOutputState(
                    intent.getStringExtra(HudBridgeStatusBroadcast.EXTRA_HUD_OUTPUT_STATE)
                ),
                espConnectionState = parseEspConnectionState(
                    intent.getStringExtra(HudBridgeStatusBroadcast.EXTRA_ESP_CONNECTION_STATE)
                ),
                lastEvent = intent.getStringExtra(HudBridgeStatusBroadcast.EXTRA_LAST_EVENT).orEmpty(),
                lastEventTimeMillis = intent.getLongExtra(
                    HudBridgeStatusBroadcast.EXTRA_LAST_EVENT_TIME_MILLIS,
                    0L
                ),
                nextEspDiscoveryRetryAtMillis = intent.getLongExtra(
                    HudBridgeStatusBroadcast.EXTRA_NEXT_ESP_DISCOVERY_RETRY_AT_MILLIS,
                    0L
                ),
                speedKmh = intent.getIntExtra(HudBridgeStatusBroadcast.EXTRA_SPEED_KMH, 0)
            )
            updateTargetView()
            renderDashboardStatus()
        }
    }

    private val androidAutoReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                HeadunitRevivedBroadcast.ACTION_PROJECTION_REQUEST -> {
                    handleAndroidAutoActive(getString(R.string.source_projection))
                }
                HeadunitRevivedBroadcast.ACTION_NAVIGATION_UPDATE -> {
                    val packet = intent.toHudNavigationPacket()
                    if (packet.activeGuidance) {
                        updateNavigationBroadcastTable(intent)
                    }
                    updateSimulatorNavigation(packet)
                    handleAndroidAutoActive(getString(R.string.source_navigation))
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        startHudBridgeService()
        buildContentView()
        registerBridgeStatusReceiver()
        registerAndroidAutoReceiver()
        updateWifiSummary()
        updateTargetView()
        updatePermissionSummary()
        renderDashboardStatus()
        startSpeedTracking()
        requestHudBridgeStatus()
        uiHandler.post(bridgeStatusTicker)
    }

    override fun onResume() {
        super.onResume()
        updatePermissionSummary()
        updateWifiSummary()
        updateTargetView()
        requestHudBridgeStatus()
    }

    override fun onDestroy() {
        unregisterAndroidAutoReceiver()
        unregisterBridgeStatusReceiver()
        uiHandler.removeCallbacks(bridgeStatusTicker)
        bleClient?.close()
        discoveryClient?.close()
        networkExecutor.shutdownNow()
        super.onDestroy()
    }

    override fun onProvisioningMessage(message: String) {
        runOnUiThread {
            statusView.text = message
        }
    }

    override fun onProvisioningComplete(ipAddress: String, udpPort: Int) {
        ProvisioningStore.saveTarget(this, ipAddress, udpPort)
        runOnUiThread {
            updateTargetView()
            statusView.text = getString(R.string.status_esp_wifi_connected, ipAddress, udpPort)
        }
        sendEsp32Settings(host = ipAddress, port = udpPort, showStatus = false)
        refreshHudBridgeState()
    }

    override fun onProvisioningReadyForDiscovery(udpPort: Int) {
        runOnUiThread {
            if (autoDiscoveryGate.onProvisioningReady()) {
                statusView.text = getString(R.string.status_android_auto_online_auto_search)
                discoverEsp32OnWifi(timeoutMillis = AUTO_DISCOVERY_TIMEOUT_MS)
            } else {
                statusView.text = getString(R.string.status_wifi_sent_waiting_headunit)
            }
        }
    }

    override fun onDiscoveryMessage(message: String) {
        runOnUiThread {
            statusView.text = message
        }
    }

    override fun onEsp32Discovered(host: String, port: Int, targetKind: HudTargetKind) {
        ProvisioningStore.saveTarget(this, host, port, targetKind)
        runOnUiThread {
            bridgeStatus = bridgeStatus.copy(
                espConnectionState = EspConnectionObservedState.CONNECTED,
                lastEvent = "esp32_discovery_found_sent",
                lastEventTimeMillis = System.currentTimeMillis(),
                nextEspDiscoveryRetryAtMillis = 0L
            )
            updateTargetView()
            renderDashboardStatus()
            statusView.text = getString(R.string.status_esp_wifi_discovery_success, host, port)
        }
        sendEsp32Settings(host = host, port = port, targetKind = targetKind, showStatus = false)
        refreshHudBridgeState()
    }

    override fun onEsp32DiscoveryFailed(message: String) {
        runOnUiThread {
            bridgeStatus = bridgeStatus.copy(
                espConnectionState = if (ProvisioningStore.targetHost(this).isNullOrBlank()) {
                    EspConnectionObservedState.DISCONNECTED
                } else {
                    EspConnectionObservedState.DISCONNECTED
                },
                lastEvent = "esp32_discovery_failed",
                lastEventTimeMillis = System.currentTimeMillis(),
                nextEspDiscoveryRetryAtMillis = 0L
            )
            renderDashboardStatus()
            statusView.text = message
        }
    }

    private fun buildContentView() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(18), dp(18), dp(24))
            setBackgroundColor(COLOR_SCREEN_BG)
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }

        root.addView(createHeader())
        root.addView(createDisplaySimulatorCard())
        root.addView(createStatusCard())
        root.addView(createWifiCard())
        root.addView(createEspCard())
        root.addView(createSettingsCard())
        root.addView(createPermissionCard())
        root.addView(createRawNavigationCard())
        root.addView(createLogCard())

        setContentView(
            ScrollView(this).apply {
                setBackgroundColor(COLOR_SCREEN_BG)
                addView(root)
            }
        )
    }

    private fun createHeader(): View {
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(4), 0, dp(16))

            addView(TextView(this@MainActivity).apply {
                text = getString(R.string.app_name)
                textSize = 26f
                setTextColor(COLOR_TEXT_PRIMARY)
                setTypeface(Typeface.DEFAULT, Typeface.BOLD)
            })
            addView(TextView(this@MainActivity).apply {
                text = getString(R.string.app_subtitle)
                textSize = 14f
                setTextColor(COLOR_TEXT_SECONDARY)
                setPadding(0, dp(4), 0, 0)
            })
        }
    }

    private fun createStatusCard(): View {
        return createCard(getString(R.string.card_status)).apply {
            headunitValueView = addStatusRow("Headunit")
            espValueView = addStatusRow("ESP32")
            hudValueView = addStatusRow(getString(R.string.status_hud_send))
            retryValueView = addStatusRow(getString(R.string.status_auto_discovery))
            eventValueView = addStatusRow(getString(R.string.status_last_event))
        }
    }

    private fun createDisplaySimulatorCard(): View {
        return createCard(getString(R.string.card_display_simulator)).apply {
            displaySimulatorView = HudDisplaySimulatorView(this@MainActivity).apply {
                updateStatus(bridgeStatus)
                updateSettings(
                    debugOverlay = ProvisioningStore.debugOverlayEnabled(this@MainActivity),
                    speedUnit = ProvisioningStore.speedUnitVisible(this@MainActivity),
                    speedFontSize = ProvisioningStore.speedFontSize(this@MainActivity),
                    hudLanguage = ProvisioningStore.hudLanguage(this@MainActivity)
                )
                layoutParams = LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
                setPadding(0, dp(2), 0, dp(2))
            }
            addView(displaySimulatorView)
        }
    }

    private fun createWifiCard(): View {
        return createCard(getString(R.string.card_hotspot_wifi)).apply {
            wifiSummaryView = TextView(this@MainActivity).apply {
                textSize = 15f
                setTextColor(COLOR_TEXT_PRIMARY)
                setPadding(0, 0, 0, dp(10))
            }
            addView(wifiSummaryView)

            wifiEditorContainer = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                visibility = View.GONE
            }

            ssidInput = EditText(this@MainActivity).apply {
                hint = getString(R.string.provisioning_ssid_hint)
                setSingleLine(true)
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
                setText(ProvisioningStore.wifiSsid(this@MainActivity))
            }
            passwordInput = EditText(this@MainActivity).apply {
                hint = getString(R.string.provisioning_password_hint)
                setSingleLine(true)
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
                setText(ProvisioningStore.wifiPassword(this@MainActivity))
            }
            wifiEditorContainer.addView(ssidInput)
            wifiEditorContainer.addView(passwordInput)
            addView(wifiEditorContainer)
            attachWifiCredentialPersistence()

            val actions = createButtonRow()
            wifiEditButton = createButton(getString(R.string.button_edit), COLOR_BUTTON_SECONDARY, COLOR_TEXT_PRIMARY) {
                setWifiEditorVisible(!wifiEditorVisible)
            }
            actions.addView(wifiEditButton)
            actions.addView(createButton(getString(R.string.provisioning_connect_button), COLOR_BUTTON_PRIMARY, Color.WHITE) {
                provisionEsp32()
            })
            addView(actions)

            setWifiEditorVisible(ProvisioningStore.wifiSsid(this@MainActivity).isBlank())
        }
    }

    private fun createEspCard(): View {
        return createCard(getString(R.string.card_esp32_target)).apply {
            targetValueView = addStatusRow(getString(R.string.status_saved_target))

            val actions = createButtonRow()
            espDiscoverButton = createButton(getString(R.string.provisioning_discover_button), COLOR_BUTTON_PRIMARY, Color.WHITE) {
                discoverEsp32OnWifi()
            }
            actions.addView(espDiscoverButton)
            actions.addView(createButton(getString(R.string.provisioning_test_button), COLOR_BUTTON_SECONDARY, COLOR_TEXT_PRIMARY) {
                sendTestPacket()
            })
            addView(actions)

            val clearActions = createButtonRow()
            clearActions.addView(createButton(getString(R.string.provisioning_clear_button), COLOR_BUTTON_DANGER_SOFT, COLOR_DANGER) {
                ProvisioningStore.clearTarget(this@MainActivity)
                updateTargetView()
                statusView.text = getString(R.string.provisioning_target_cleared)
            })
            addView(clearActions)
        }
    }

    private fun createSettingsCard(): View {
        return createCard(getString(R.string.card_hud_settings)).apply {
            debugSwitch = Switch(this@MainActivity).apply {
                text = getString(R.string.debug_overlay_switch)
                textSize = 15f
                setTextColor(COLOR_TEXT_PRIMARY)
                isChecked = ProvisioningStore.debugOverlayEnabled(this@MainActivity)
                setPadding(0, 0, 0, dp(8))
                setOnCheckedChangeListener { _, isChecked ->
                    ProvisioningStore.saveDebugOverlayEnabled(this@MainActivity, isChecked)
                    updateSimulatorSettings()
                    sendEsp32Settings()
                }
            }
            addView(debugSwitch)

            speedUnitSwitch = Switch(this@MainActivity).apply {
                text = getString(R.string.speed_unit_switch)
                textSize = 15f
                setTextColor(COLOR_TEXT_PRIMARY)
                isChecked = ProvisioningStore.speedUnitVisible(this@MainActivity)
                setPadding(0, 0, 0, dp(8))
                setOnCheckedChangeListener { _, isChecked ->
                    ProvisioningStore.saveSpeedUnitVisible(this@MainActivity, isChecked)
                    updateSimulatorSettings()
                    sendEsp32Settings()
                }
            }
            addView(speedUnitSwitch)

            addView(createHudLanguageControl())
            addView(createSpeedFontSizeControl())
        }
    }

    private fun createHudLanguageControl(): View {
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(2), 0, dp(8))
        }
        container.addView(TextView(this).apply {
            text = getString(R.string.label_hud_language)
            textSize = 15f
            setTextColor(COLOR_TEXT_PRIMARY)
        })

        val koreanId = View.generateViewId()
        val englishId = View.generateViewId()
        val current = ProvisioningStore.hudLanguage(this)
        val group = RadioGroup(this).apply {
            orientation = RadioGroup.HORIZONTAL
            setPadding(0, dp(4), 0, 0)
        }
        group.addView(RadioButton(this).apply {
            id = koreanId
            text = getString(R.string.language_korean)
            setTextColor(COLOR_TEXT_PRIMARY)
        })
        group.addView(RadioButton(this).apply {
            id = englishId
            text = getString(R.string.language_english)
            setTextColor(COLOR_TEXT_PRIMARY)
        })
        group.check(if (current == Esp32SettingsPacket.LANGUAGE_ENGLISH) englishId else koreanId)
        group.setOnCheckedChangeListener { _, checkedId ->
            val language = if (checkedId == englishId) {
                Esp32SettingsPacket.LANGUAGE_ENGLISH
            } else {
                Esp32SettingsPacket.LANGUAGE_KOREAN
            }
            if (language == ProvisioningStore.hudLanguage(this@MainActivity)) {
                return@setOnCheckedChangeListener
            }
            ProvisioningStore.saveHudLanguage(this@MainActivity, language)
            updateSimulatorSettings()
            sendEsp32Settings()
            recreate()
        }
        container.addView(group)
        return container
    }

    private fun createSpeedFontSizeControl(): View {
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(2), 0, dp(4))
        }
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        header.addView(TextView(this).apply {
            text = getString(R.string.label_speed_font_size)
            textSize = 15f
            setTextColor(COLOR_TEXT_PRIMARY)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        })
        speedFontSizeValueView = TextView(this).apply {
            textSize = 15f
            setTextColor(COLOR_TEXT_SECONDARY)
            gravity = Gravity.END
        }
        header.addView(speedFontSizeValueView)
        container.addView(header)

        val current = ProvisioningStore.speedFontSize(this)
        speedFontSizeValueView.text = "${current}x"
        container.addView(SeekBar(this).apply {
            max = Esp32SettingsPacket.MAX_SPEED_FONT_SIZE - Esp32SettingsPacket.MIN_SPEED_FONT_SIZE
            progress = current - Esp32SettingsPacket.MIN_SPEED_FONT_SIZE
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                    val value = progress + Esp32SettingsPacket.MIN_SPEED_FONT_SIZE
                    speedFontSizeValueView.text = "${value}x"
                    if (fromUser) {
                        ProvisioningStore.saveSpeedFontSize(this@MainActivity, value)
                        updateSimulatorSettings()
                        sendEsp32Settings()
                    }
                }

                override fun onStartTrackingTouch(seekBar: SeekBar?) = Unit
                override fun onStopTrackingTouch(seekBar: SeekBar?) = Unit
            })
        })
        return container
    }

    private fun createPermissionCard(): View {
        return createCard(getString(R.string.card_permissions)).apply {
            permissionAllowedView = addStatusRow(getString(R.string.permission_allowed))
            permissionDeniedView = addStatusRow(getString(R.string.permission_denied))
            backgroundValueView = addStatusRow(getString(R.string.permission_battery))

            permissionActionsRow = createButtonRow()
            runtimePermissionButton = createButton(getString(R.string.button_request_permissions), COLOR_BUTTON_SECONDARY, COLOR_TEXT_PRIMARY) {
                if (!requestMissingRuntimePermissions()) {
                    showToast(R.string.runtime_permissions_already_allowed)
                }
                updatePermissionSummary()
            }
            permissionActionsRow.addView(runtimePermissionButton)
            batteryOptimizationButton = createButton(getString(R.string.button_allow_background), COLOR_BUTTON_PRIMARY, Color.WHITE) {
                requestBatteryOptimizationExemption()
            }
            permissionActionsRow.addView(batteryOptimizationButton)
            addView(permissionActionsRow)
        }
    }

    private fun createRawNavigationCard(): View {
        return createCard(getString(R.string.card_raw_navigation)).apply {
            rawNavigationValueViews.clear()
            rawNavigationTable = TableLayout(this@MainActivity).apply {
                isStretchAllColumns = true
                isShrinkAllColumns = true
            }
            rawNavigationTable.addView(TableRow(this@MainActivity).apply {
                addView(createRawNavigationCell(getString(R.string.raw_table_field), isHeader = true, weight = 0.24f))
                addView(createRawNavigationCell(getString(R.string.raw_table_description), isHeader = true, weight = 0.15f))
                addView(createRawNavigationCell(getString(R.string.raw_table_value), isHeader = true, weight = 0.61f))
            })
            RAW_NAVIGATION_FIELDS.forEach { field ->
                val valueView = createRawNavigationCell("-", isHeader = false, weight = 0.61f)
                rawNavigationValueViews[field.variable] = valueView
                rawNavigationTable.addView(TableRow(this@MainActivity).apply {
                    addView(createRawNavigationCell(field.variable, isHeader = false, weight = 0.24f))
                    addView(createRawNavigationCell(getString(field.descriptionResId), isHeader = false, weight = 0.15f))
                    addView(valueView)
                })
            }
            addView(rawNavigationTable)
        }
    }

    private fun createRawNavigationCell(textValue: String, isHeader: Boolean, weight: Float): TextView {
        return TextView(this).apply {
            text = textValue
            textSize = if (isHeader) 12f else 13f
            setTextColor(if (isHeader) Color.WHITE else COLOR_TEXT_PRIMARY)
            setTypeface(Typeface.MONOSPACE, if (isHeader) Typeface.BOLD else Typeface.NORMAL)
            setPadding(dp(8), dp(6), dp(8), dp(6))
            setSingleLine(false)
            layoutParams = TableRow.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, weight)
            background = roundedRect(
                if (isHeader) Color.rgb(22, 31, 43) else Color.rgb(248, 250, 252),
                dp(2).toFloat()
            )
        }
    }

    private fun createLogCard(): View {
        return createCard(getString(R.string.card_log)).apply {
            statusView = TextView(this@MainActivity).apply {
                text = getString(R.string.provisioning_idle)
                textSize = 15f
                setTextColor(COLOR_TEXT_PRIMARY)
                setLineSpacing(0f, 1.1f)
            }
            addView(statusView)
        }
    }

    private fun createCard(title: String): LinearLayout {
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(14), dp(16), dp(16))
            background = roundedRect(COLOR_CARD_BG, dp(16).toFloat())
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply {
                bottomMargin = dp(12)
            }

            addView(TextView(this@MainActivity).apply {
                text = title
                textSize = 17f
                setTextColor(COLOR_TEXT_PRIMARY)
                setTypeface(Typeface.DEFAULT, Typeface.BOLD)
                setPadding(0, 0, 0, dp(10))
            })
        }
    }

    private fun LinearLayout.addStatusRow(label: String): TextView {
        val row = LinearLayout(this@MainActivity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(3), 0, dp(3))
        }
        val labelView = TextView(this@MainActivity).apply {
            text = label
            textSize = 13f
            setTextColor(COLOR_TEXT_MUTED)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 0.36f)
        }
        val valueView = TextView(this@MainActivity).apply {
            text = "-"
            textSize = 15f
            setTextColor(COLOR_TEXT_PRIMARY)
            gravity = Gravity.END
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 0.64f)
        }
        row.addView(labelView)
        row.addView(valueView)
        addView(row)
        return valueView
    }

    private fun createButtonRow(): LinearLayout {
        return LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, dp(8), 0, dp(4))
        }
    }

    private fun createButton(
        textValue: String,
        backgroundColor: Int,
        textColor: Int,
        onClick: () -> Unit
    ): Button {
        return Button(this).apply {
            text = textValue
            textSize = 14f
            isAllCaps = false
            setTextColor(textColor)
            background = roundedRect(backgroundColor, dp(12).toFloat())
            minHeight = dp(44)
            setPadding(dp(12), 0, dp(12), 0)
            layoutParams = LinearLayout.LayoutParams(0, dp(46), 1f).apply {
                rightMargin = dp(8)
            }
            setOnClickListener { onClick() }
        }
    }

    private fun setWifiEditorVisible(visible: Boolean) {
        wifiEditorVisible = visible
        if (::wifiEditorContainer.isInitialized) {
            wifiEditorContainer.visibility = if (visible) View.VISIBLE else View.GONE
        }
        if (::wifiEditButton.isInitialized) {
            wifiEditButton.text = if (visible) getString(R.string.button_close) else getString(R.string.button_edit)
        }
    }

    private fun provisionEsp32() {
        if (requestMissingRuntimePermissions()) {
            updatePermissionSummary()
            statusView.text = getString(R.string.provisioning_permissions_needed)
            return
        }

        val ssid = ssidInput.text.toString().trim()
        if (ssid.isBlank()) {
            setWifiEditorVisible(true)
            statusView.text = getString(R.string.provisioning_ssid_required)
            return
        }
        val password = passwordInput.text.toString()
        ProvisioningStore.saveWifiCredentials(this, ssid, password)
        updateWifiSummary()

        val credentials = WifiCredentialsPacket(
            ssid = ssid,
            password = password,
            udpPort = BleProvisioningContract.DEFAULT_UDP_PORT
        )

        bleClient?.close()
        bleClient = BleProvisioningClient(applicationContext, this)
        bleClient?.provision(credentials)
    }

    private fun attachWifiCredentialPersistence() {
        val watcher = object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit

            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                ProvisioningStore.saveWifiCredentials(
                    this@MainActivity,
                    ssidInput.text.toString(),
                    passwordInput.text.toString()
                )
                updateWifiSummary()
            }

            override fun afterTextChanged(s: Editable?) = Unit
        }
        ssidInput.addTextChangedListener(watcher)
        passwordInput.addTextChangedListener(watcher)
    }

    private fun discoverEsp32OnWifi(timeoutMillis: Long = MANUAL_DISCOVERY_TIMEOUT_MS) {
        bridgeStatus = bridgeStatus.copy(
            espConnectionState = EspConnectionObservedState.DISCOVERING,
            lastEvent = "esp32_discovery_started",
            lastEventTimeMillis = System.currentTimeMillis(),
            nextEspDiscoveryRetryAtMillis = 0L
        )
        renderDashboardStatus()
        discoveryClient?.close()
        discoveryClient = Esp32DiscoveryClient(applicationContext, this)
        discoveryClient?.start(timeoutMillis)
    }

    private fun handleAndroidAutoActive(source: String) {
        if (!autoDiscoveryGate.onAndroidAutoActive()) {
            return
        }

        statusView.text = getString(R.string.status_android_auto_source_online, source)
        discoverEsp32OnWifi(timeoutMillis = AUTO_DISCOVERY_TIMEOUT_MS)
    }

    private fun registerAndroidAutoReceiver() {
        if (androidAutoReceiverRegistered) {
            return
        }

        val filter = IntentFilter().apply {
            addAction(HeadunitRevivedBroadcast.ACTION_PROJECTION_REQUEST)
            addAction(HeadunitRevivedBroadcast.ACTION_NAVIGATION_UPDATE)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(androidAutoReceiver, filter, Context.RECEIVER_EXPORTED)
        } else {
            registerReceiver(androidAutoReceiver, filter)
        }
        androidAutoReceiverRegistered = true
    }

    private fun updateNavigationBroadcastTable(intent: Intent) {
        if (!::rawNavigationTable.isInitialized) {
            return
        }
        navigationBroadcastValues(intent).forEach { value ->
            rawNavigationValueViews[value.variable]?.text = value.value.ifBlank { "-" }
        }
    }

    private fun updateSimulatorNavigation(packet: HudNavigationPacket) {
        if (::displaySimulatorView.isInitialized) {
            displaySimulatorView.updateNavigation(packet.withRenderedHudBitmaps())
        }
    }

    private fun updateSimulatorSettings() {
        if (::displaySimulatorView.isInitialized) {
            displaySimulatorView.updateSettings(
                debugOverlay = ProvisioningStore.debugOverlayEnabled(this),
                speedUnit = ProvisioningStore.speedUnitVisible(this),
                speedFontSize = ProvisioningStore.speedFontSize(this),
                hudLanguage = ProvisioningStore.hudLanguage(this)
            )
        }
    }

    private fun navigationBroadcastValues(intent: Intent): List<NavigationBroadcastValue> {
        return listOf(
            NavigationBroadcastValue("distance_meters", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_DISTANCE_METERS, -1).toString()),
            NavigationBroadcastValue("time_seconds", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_TIME_SECONDS, -1).toString()),
            NavigationBroadcastValue("next_event_type", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_NEXT_EVENT_TYPE, -1).toString()),
            NavigationBroadcastValue("turn_side", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_TURN_SIDE, -1).toString()),
            NavigationBroadcastValue("road", intent.getStringExtra(HeadunitRevivedBroadcast.EXTRA_ROAD).orEmpty()),
            NavigationBroadcastValue("action_text", intent.getStringExtra(HeadunitRevivedBroadcast.EXTRA_ACTION_TEXT).orEmpty()),
            NavigationBroadcastValue("turn_number", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_TURN_NUMBER, -1).toString()),
            NavigationBroadcastValue("turn_angle", intent.getIntExtra(HeadunitRevivedBroadcast.EXTRA_TURN_ANGLE, -1).toString()),
            NavigationBroadcastValue("cluster_age_ms", intent.getLongExtra(HeadunitRevivedBroadcast.EXTRA_CLUSTER_AGE_MS, -1L).displayDebugAge()),
            NavigationBroadcastValue("turn_detail_age_ms", intent.getLongExtra(HeadunitRevivedBroadcast.EXTRA_TURN_DETAIL_AGE_MS, -1L).displayDebugAge()),
            NavigationBroadcastValue("turn_distance_age_ms", intent.getLongExtra(HeadunitRevivedBroadcast.EXTRA_TURN_DISTANCE_AGE_MS, -1L).displayDebugAge())
        )
    }

    private fun Long.displayDebugAge(): String {
        return if (this < 0L) "-" else "${this}ms"
    }

    private fun unregisterAndroidAutoReceiver() {
        if (!androidAutoReceiverRegistered) {
            return
        }

        unregisterReceiver(androidAutoReceiver)
        androidAutoReceiverRegistered = false
    }

    private fun registerBridgeStatusReceiver() {
        if (bridgeStatusReceiverRegistered) {
            return
        }

        val filter = IntentFilter(HudBridgeStatusBroadcast.ACTION_BRIDGE_STATUS)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(bridgeStatusReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(bridgeStatusReceiver, filter)
        }
        bridgeStatusReceiverRegistered = true
    }

    private fun unregisterBridgeStatusReceiver() {
        if (!bridgeStatusReceiverRegistered) {
            return
        }

        unregisterReceiver(bridgeStatusReceiver)
        bridgeStatusReceiverRegistered = false
    }

    private fun renderDashboardStatus() {
        if (!::headunitValueView.isInitialized) {
            return
        }

        val nowMillis = System.currentTimeMillis()
        headunitValueView.text = bridgeStatus.headunitDisplayText().animatedProgress(nowMillis)
        headunitValueView.setTextColor(
            if (bridgeStatus.headunitOnline) COLOR_SUCCESS else COLOR_WARNING
        )

        espValueView.text = bridgeStatus.espDisplayText().animatedProgress(nowMillis)
        espValueView.setTextColor(bridgeStatus.espDisplayColor())

        hudValueView.text = bridgeStatus.hudOutputState.displayText().animatedProgress(nowMillis)
        retryValueView.text = bridgeStatus.retryDisplayText().animatedProgress(nowMillis)
        eventValueView.text = "${bridgeStatus.lastEvent.displayEventText()} · ${bridgeStatus.lastEventTimeMillis.displayAge()}"
            .animatedProgress(nowMillis)
        if (::statusView.isInitialized) {
            statusView.text = statusView.text.toString().animatedProgress(nowMillis)
        }
        if (::espDiscoverButton.isInitialized) {
            espDiscoverButton.text = getString(
                if (bridgeStatus.espConnectionState == EspConnectionObservedState.DISCOVERING) {
                    R.string.provisioning_discover_button_running
                } else {
                    R.string.provisioning_discover_button
                }
            ).animatedProgress(nowMillis)
        }
        if (::displaySimulatorView.isInitialized) {
            displaySimulatorView.updateStatus(bridgeStatus)
        }
    }

    private fun parseHeadunitState(value: String?): HeadunitObservedState {
        return value?.let {
            runCatching { HeadunitObservedState.valueOf(it) }.getOrNull()
        } ?: HeadunitObservedState.WAITING_FOR_BROADCAST
    }

    private fun parseHudOutputState(value: String?): HudOutputState {
        return value?.let {
            runCatching { HudOutputState.valueOf(it) }.getOrNull()
        } ?: HudOutputState.NONE
    }

    private fun parseEspConnectionState(value: String?): EspConnectionObservedState {
        return value?.let {
            runCatching { EspConnectionObservedState.valueOf(it) }.getOrNull()
        } ?: EspConnectionObservedState.DISCONNECTED
    }

    private fun BridgeDashboardStatus.headunitDisplayText(): String {
        return when (headunitState) {
            HeadunitObservedState.WAITING_FOR_BROADCAST -> getString(R.string.headunit_waiting)
            HeadunitObservedState.PROJECTION_ACTIVE -> getString(R.string.headunit_projection_active)
            HeadunitObservedState.NAVIGATION_ACTIVE -> getString(R.string.headunit_navigation_active)
        }
    }

    private fun BridgeDashboardStatus.espDisplayText(): String {
        return when (espConnectionState) {
            EspConnectionObservedState.CONNECTED -> getString(R.string.esp_connected)
            EspConnectionObservedState.DISCOVERING -> getString(R.string.esp_discovering)
            EspConnectionObservedState.RETRY_WAITING -> {
                val seconds = retrySecondsRemaining(System.currentTimeMillis())
                if (seconds == null) {
                    getString(R.string.esp_retry_waiting)
                } else {
                    getString(R.string.esp_retry_seconds, seconds)
                }
            }
            EspConnectionObservedState.DISCONNECTED -> {
                if (ProvisioningStore.targetHost(this@MainActivity).isNullOrBlank()) {
                    getString(R.string.esp_no_saved_target)
                } else {
                    getString(R.string.esp_pending_check)
                }
            }
        }
    }

    private fun BridgeDashboardStatus.espDisplayColor(): Int {
        return when (espConnectionState) {
            EspConnectionObservedState.CONNECTED -> COLOR_SUCCESS
            EspConnectionObservedState.DISCOVERING,
            EspConnectionObservedState.RETRY_WAITING -> COLOR_WARNING
            EspConnectionObservedState.DISCONNECTED -> COLOR_DANGER
        }
    }

    private fun BridgeDashboardStatus.retryDisplayText(): String {
        val retrySeconds = retrySecondsRemaining(System.currentTimeMillis())
        return when {
            retrySeconds != null -> getString(R.string.retry_seconds, retrySeconds)
            espConnectionState == EspConnectionObservedState.DISCOVERING -> getString(R.string.retry_in_progress)
            headunitOnline -> getString(R.string.retry_auto_when_headunit)
            else -> getString(R.string.retry_after_headunit)
        }
    }

    private fun HudOutputState.displayText(): String {
        return when (this) {
            HudOutputState.NONE -> getString(R.string.hud_output_none)
            HudOutputState.NAVIGATION_GUIDANCE -> getString(R.string.hud_output_guidance)
            HudOutputState.NAVIGATION_INACTIVE -> getString(R.string.hud_output_inactive)
        }
    }

    private fun String.displayEventText(): String {
        return when (this) {
            "service_started" -> getString(R.string.event_service_started)
            "status_request" -> getString(R.string.event_status_request)
            "refresh_no_headunit_state" -> getString(R.string.event_refresh_no_headunit_state)
            "refresh_sent" -> getString(R.string.event_refresh_sent)
            "refresh_failed" -> getString(R.string.event_refresh_failed)
            "projection_sent" -> getString(R.string.event_projection_sent)
            "projection_failed" -> getString(R.string.event_projection_failed)
            "navigation_sent" -> getString(R.string.event_navigation_sent)
            "navigation_failed" -> getString(R.string.event_navigation_failed)
            "esp32_discovery_started" -> getString(R.string.event_esp32_discovery_started)
            "esp32_discovery_found_sent" -> getString(R.string.event_esp32_discovery_found_sent)
            "esp32_discovery_found_failed" -> getString(R.string.event_esp32_discovery_found_failed)
            "esp32_discovery_failed" -> getString(R.string.event_esp32_discovery_failed)
            "esp32_connected" -> getString(R.string.event_esp32_connected)
            "esp32_disconnected" -> getString(R.string.event_esp32_disconnected)
            "test_packet_preview" -> getString(R.string.event_test_packet_preview)
            else -> getString(R.string.event_none)
        }
    }

    private fun Long.displayAge(): String {
        if (this <= 0L) {
            return getString(R.string.age_never)
        }

        val seconds = ((System.currentTimeMillis() - this).coerceAtLeast(0L) / 1000L).toInt()
        return if (seconds < 60) {
            getString(R.string.age_seconds, seconds)
        } else {
            getString(R.string.age_minutes_seconds, seconds / 60, seconds % 60)
        }
    }

    private fun String.animatedProgress(nowMillis: Long): String {
        return ProgressTextAnimator.animate(this, nowMillis)
    }

    private fun sendEsp32Settings(
        host: String? = ProvisioningStore.targetHost(this),
        port: Int = ProvisioningStore.targetPort(this),
        targetKind: HudTargetKind = ProvisioningStore.targetKind(this),
        showStatus: Boolean = true
    ) {
        if (host.isNullOrBlank()) {
            if (showStatus) {
                statusView.text = getString(R.string.debug_overlay_saved_waiting)
            }
            return
        }
        if (!targetKind.receivesEsp32Settings) {
            return
        }

        val packet = Esp32SettingsPacket(
            debugOverlay = ProvisioningStore.debugOverlayEnabled(this),
            speedUnitVisible = ProvisioningStore.speedUnitVisible(this),
            speedFontSize = ProvisioningStore.speedFontSize(this),
            hudLanguage = ProvisioningStore.hudLanguage(this)
        )
        networkExecutor.execute {
            runCatching {
                sendPacketToTargets(host, port, packet.toJson())
            }.onSuccess {
                if (showStatus) {
                    runOnUiThread {
                        statusView.text = if (it.all(UdpHudSendResult::sent)) {
                            getString(R.string.status_settings_sent)
                        } else {
                            getString(R.string.status_settings_partial_failed)
                        }
                    }
                }
            }.onFailure { error ->
                if (showStatus) {
                    runOnUiThread {
                        statusView.text = getString(R.string.status_settings_failed, error.message.orEmpty())
                    }
                }
            }
        }
    }

    private fun requestBatteryOptimizationExemption() {
        val powerManager = getSystemService(PowerManager::class.java)
        if (powerManager?.isIgnoringBatteryOptimizations(packageName) == true) {
            statusView.text = getString(R.string.battery_optimization_already_ignored)
            showToast(R.string.battery_optimization_already_ignored)
            updatePermissionSummary()
            return
        }

        val requestIntent = Intent(
            Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
            Uri.parse("package:$packageName")
        )
        runCatching {
            startActivity(requestIntent)
        }.onFailure {
            startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        }
    }

    private fun sendTestPacket() {
        val host = ProvisioningStore.targetHost(this)
        val port = ProvisioningStore.targetPort(this)
        if (host.isNullOrBlank()) {
            statusView.text = getString(R.string.provisioning_connect_first)
            return
        }

        val packet = HudNavigationPacket.fromHeadunitValues(
            distanceMeters = 300,
            timeSeconds = 25,
            road = "HUD TEST",
            nextEventType = HeadunitNavEvent.TURN.wireValue,
            turnSide = TurnSide.RIGHT.wireValue,
            turnNumber = -1,
            turnAngle = -1
        ).withRenderedHudBitmaps()
        bridgeStatus = bridgeStatus.copy(
            headunitState = HeadunitObservedState.NAVIGATION_ACTIVE,
            hudOutputState = HudOutputState.NAVIGATION_GUIDANCE,
            lastEvent = "test_packet_preview",
            lastEventTimeMillis = System.currentTimeMillis()
        )
        renderDashboardStatus()
        updateSimulatorNavigation(packet)

        networkExecutor.execute {
            runCatching {
                sendPacketToTargets(host, port, packet.toHudJson())
            }.onSuccess {
                runOnUiThread {
                    statusView.text = if (it.all(UdpHudSendResult::sent)) {
                        getString(R.string.status_test_sent, host, port)
                    } else {
                        getString(R.string.status_test_partial_failed)
                    }
                }
            }.onFailure { error ->
                runOnUiThread {
                    statusView.text = getString(R.string.status_test_failed, error.message.orEmpty())
                }
            }
        }
    }

    private fun sendPacketToTargets(host: String, port: Int, payload: String): List<UdpHudSendResult> {
        val sequencedPayload = HudUdpPayloadSequencer.wrap(payload, SystemClock.elapsedRealtime())
        return HudUdpTargetPlan.forTarget(host, port).map { target ->
            UdpHudSender(target.host, target.port).sendFireAndForget(sequencedPayload)
        }
    }

    private fun updateTargetView() {
        if (!::targetValueView.isInitialized) {
            return
        }
        val host = ProvisioningStore.targetHost(this)
        val port = ProvisioningStore.targetPort(this)
        targetValueView.text = if (host.isNullOrBlank()) {
            getString(R.string.none)
        } else {
            String.format(Locale.US, "%s:%d", host, port)
        }
    }

    private fun updateWifiSummary() {
        if (!::wifiSummaryView.isInitialized) {
            return
        }
        val ssid = ProvisioningStore.wifiSsid(this).ifBlank { getString(R.string.not_set) }
        val passwordState = if (ProvisioningStore.wifiPassword(this).isBlank()) {
            getString(R.string.password_empty)
        } else {
            getString(R.string.password_saved)
        }
        wifiSummaryView.text = "SSID: $ssid\n$passwordState"
    }

    private fun updatePermissionSummary() {
        if (!::permissionAllowedView.isInitialized) {
            return
        }
        val required = requiredRuntimePermissions()
        val allowed = required
            .filter { checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED }
            .map(::permissionDisplayName)
        val denied = required
            .filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
            .map(::permissionDisplayName)

        permissionAllowedView.text = allowed.joinToString(", ").ifBlank { getString(R.string.none) }
        permissionDeniedView.text = denied.joinToString(", ").ifBlank { getString(R.string.none) }
        permissionDeniedView.setTextColor(if (denied.isEmpty()) COLOR_SUCCESS else COLOR_DANGER)

        val powerManager = getSystemService(PowerManager::class.java)
        val ignored = powerManager?.isIgnoringBatteryOptimizations(packageName) == true
        backgroundValueView.text = if (ignored) {
            getString(R.string.battery_ignored)
        } else {
            getString(R.string.battery_restricted)
        }
        backgroundValueView.setTextColor(if (ignored) COLOR_SUCCESS else COLOR_WARNING)

        updatePermissionActionVisibility(
            PermissionActionVisibility.from(
                missingRuntimePermissionCount = denied.size,
                batteryOptimizationIgnored = ignored
            )
        )
    }

    private fun updatePermissionActionVisibility(visibility: PermissionActionVisibility) {
        if (!::permissionActionsRow.isInitialized) {
            return
        }

        runtimePermissionButton.visibility = if (visibility.showRuntimePermissionButton) View.VISIBLE else View.GONE
        batteryOptimizationButton.visibility = if (visibility.showBatteryOptimizationButton) View.VISIBLE else View.GONE
        permissionActionsRow.visibility = if (visibility.showActionsRow) View.VISIBLE else View.GONE
    }

    private fun requestMissingRuntimePermissions(): Boolean {
        val missing = requiredRuntimePermissions()
            .filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }

        if (missing.isNotEmpty()) {
            requestPermissions(missing.toTypedArray(), REQUEST_RUNTIME_PERMISSIONS)
            return true
        }

        return false
    }

    private fun showToast(messageResId: Int) {
        Toast.makeText(this, getString(messageResId), Toast.LENGTH_SHORT).show()
    }

    private fun requiredRuntimePermissions(): List<String> {
        val permissions = mutableListOf<String>()
        permissions += Manifest.permission.ACCESS_FINE_LOCATION
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions += Manifest.permission.BLUETOOTH_SCAN
            permissions += Manifest.permission.BLUETOOTH_CONNECT
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
        }
        return permissions
    }

    private fun permissionDisplayName(permission: String): String {
        return when (permission) {
            Manifest.permission.ACCESS_FINE_LOCATION -> getString(R.string.permission_location)
            Manifest.permission.BLUETOOTH_SCAN -> getString(R.string.permission_bluetooth_scan)
            Manifest.permission.BLUETOOTH_CONNECT -> getString(R.string.permission_bluetooth_connect)
            Manifest.permission.POST_NOTIFICATIONS -> getString(R.string.permission_notifications)
            else -> permission.substringAfterLast('.')
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_RUNTIME_PERMISSIONS) {
            updatePermissionSummary()
            startSpeedTracking()
        }
    }

    private fun startHudBridgeService(action: String? = null) {
        val intent = Intent(this, HudBridgeService::class.java).apply {
            this.action = action
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun refreshHudBridgeState() {
        startHudBridgeService(HudBridgeService.ACTION_REFRESH_STATE)
    }

    private fun requestHudBridgeStatus() {
        startHudBridgeService(HudBridgeService.ACTION_PUBLISH_STATUS)
    }

    private fun startSpeedTracking() {
        startHudBridgeService(HudBridgeService.ACTION_START_SPEED_TRACKING)
    }

    private fun roundedRect(color: Int, radius: Float): GradientDrawable {
        return GradientDrawable().apply {
            setColor(color)
            cornerRadius = radius
        }
    }

    private fun dp(value: Int): Int {
        return (value * resources.displayMetrics.density).toInt()
    }

    companion object {
        private const val REQUEST_RUNTIME_PERMISSIONS = 100
        private const val MANUAL_DISCOVERY_TIMEOUT_MS = 12_000L
        private const val AUTO_DISCOVERY_TIMEOUT_MS = 30_000L
        private const val STATUS_TICK_INTERVAL_MS = 500L

        private val COLOR_SCREEN_BG = Color.rgb(242, 244, 247)
        private val COLOR_CARD_BG = Color.WHITE
        private val COLOR_TEXT_PRIMARY = Color.rgb(24, 32, 43)
        private val COLOR_TEXT_SECONDARY = Color.rgb(83, 96, 112)
        private val COLOR_TEXT_MUTED = Color.rgb(114, 126, 142)
        private val COLOR_BUTTON_PRIMARY = Color.rgb(20, 113, 245)
        private val COLOR_BUTTON_SECONDARY = Color.rgb(229, 235, 244)
        private val COLOR_BUTTON_DANGER_SOFT = Color.rgb(255, 232, 232)
        private val COLOR_SUCCESS = Color.rgb(17, 139, 80)
        private val COLOR_WARNING = Color.rgb(184, 110, 0)
        private val COLOR_DANGER = Color.rgb(197, 48, 48)
        private val RAW_NAVIGATION_FIELDS = listOf(
            RawNavigationField("distance_meters", R.string.raw_field_distance_meters),
            RawNavigationField("time_seconds", R.string.raw_field_time_seconds),
            RawNavigationField("next_event_type", R.string.raw_field_next_event_type),
            RawNavigationField("turn_side", R.string.raw_field_turn_side),
            RawNavigationField("road", R.string.raw_field_road),
            RawNavigationField("action_text", R.string.raw_field_action_text),
            RawNavigationField("turn_number", R.string.raw_field_turn_number),
            RawNavigationField("turn_angle", R.string.raw_field_turn_angle),
            RawNavigationField("cluster_age_ms", R.string.raw_field_cluster_age_ms),
            RawNavigationField("turn_detail_age_ms", R.string.raw_field_turn_detail_age_ms),
            RawNavigationField("turn_distance_age_ms", R.string.raw_field_turn_distance_age_ms)
        )
    }
}
