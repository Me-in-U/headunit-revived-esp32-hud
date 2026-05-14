package com.zoelowell.headunithudbridge

import android.content.Context
import android.net.wifi.WifiManager
import android.util.Log
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.SocketTimeoutException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class Esp32DiscoveryClient(
    context: Context,
    private val listener: Listener
) {
    interface Listener {
        fun onDiscoveryMessage(message: String)
        fun onEsp32Discovered(host: String, port: Int)
        fun onEsp32DiscoveryFailed(message: String)
    }

    private val appContext = context.applicationContext
    private val localizedContext = appContext.withHudLocale()
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()
    private val running = AtomicBoolean(false)

    fun start(timeoutMillis: Long = 12_000L) {
        if (!running.compareAndSet(false, true)) {
            return
        }
        executor.execute {
            discover(timeoutMillis)
        }
    }

    fun close() {
        running.set(false)
        executor.shutdownNow()
    }

    private fun discover(timeoutMillis: Long) {
        val multicastLock = appContext
            .getSystemService(WifiManager::class.java)
            ?.createMulticastLock("headunit-hud-discovery")
            ?.apply { setReferenceCounted(false) }

        try {
            multicastLock?.acquire()
            DatagramSocket(null).use { socket ->
                socket.reuseAddress = true
                socket.broadcast = true
                socket.soTimeout = RECEIVE_TIMEOUT_MS
                socket.bind(InetSocketAddress(Esp32DiscoveryPacket.DISCOVERY_PORT))

                listener.onDiscoveryMessage(
                    localizedContext.getString(R.string.discovery_searching, Esp32DiscoveryPacket.DISCOVERY_PORT)
                )
                sendProbes(socket)

                val deadline = System.currentTimeMillis() + timeoutMillis
                val buffer = ByteArray(BUFFER_SIZE)
                while (running.get() && System.currentTimeMillis() < deadline) {
                    val packet = DatagramPacket(buffer, buffer.size)
                    try {
                        socket.receive(packet)
                    } catch (_: SocketTimeoutException) {
                        sendProbes(socket)
                        continue
                    }

                    val result = parseBeacon(packet)
                    if (result != null) {
                        listener.onEsp32Discovered(result.host, result.port)
                        return
                    }
                }
                listener.onEsp32DiscoveryFailed(localizedContext.getString(R.string.discovery_timeout))
            }
        } catch (error: Exception) {
            listener.onEsp32DiscoveryFailed(
                localizedContext.getString(R.string.discovery_failed, error.message.orEmpty())
            )
        } finally {
            running.set(false)
            if (multicastLock?.isHeld == true) {
                multicastLock.release()
            }
        }
    }

    private fun sendProbes(socket: DatagramSocket) {
        discoveryProbeTargets().forEach { address ->
            sendProbe(socket, address)
        }
    }

    private fun sendProbe(socket: DatagramSocket, address: InetAddress) {
        val payload = Esp32DiscoveryPacket.discoveryProbeJson().toByteArray(Charsets.UTF_8)
        val packet = DatagramPacket(
            payload,
            payload.size,
            address,
            Esp32DiscoveryPacket.DISCOVERY_PORT
        )
        runCatching {
            socket.send(packet)
        }.onFailure { error ->
            Log.w(TAG, "ESP32 discovery probe failed to ${address.hostAddress}: ${error.message}")
        }
    }

    private fun discoveryProbeTargets(): List<InetAddress> {
        val targets = mutableListOf<InetAddress>()
        targets += InetAddress.getByName(BROADCAST_ADDRESS)
        subnetBroadcastAddress()?.let { targets += it }
        ProvisioningStore.targetHost(appContext)
            ?.takeIf { it != BROADCAST_ADDRESS }
            ?.let { host ->
                runCatching { InetAddress.getByName(host) }.getOrNull()
            }
            ?.let { targets += it }

        return targets.distinctBy { it.hostAddress }
    }

    @Suppress("DEPRECATION")
    private fun subnetBroadcastAddress(): InetAddress? {
        val dhcpInfo = appContext
            .getSystemService(WifiManager::class.java)
            ?.dhcpInfo
            ?: return null
        if (dhcpInfo.ipAddress == 0 || dhcpInfo.netmask == 0) {
            return null
        }

        val broadcast = dhcpInfo.ipAddress or dhcpInfo.netmask.inv()
        return runCatching { littleEndianInetAddress(broadcast) }.getOrNull()
    }

    private fun littleEndianInetAddress(address: Int): InetAddress {
        val bytes = byteArrayOf(
            (address and 0xff).toByte(),
            ((address shr 8) and 0xff).toByte(),
            ((address shr 16) and 0xff).toByte(),
            ((address shr 24) and 0xff).toByte()
        )
        return InetAddress.getByAddress(bytes)
    }

    private fun parseBeacon(packet: DatagramPacket): DiscoveryResult? {
        val body = String(packet.data, packet.offset, packet.length, Charsets.UTF_8)
        val json = runCatching { JSONObject(body) }.getOrNull() ?: return null
        if (json.optString(Esp32DiscoveryPacket.FIELD_TYPE) != Esp32DiscoveryPacket.TYPE_HELLO) {
            return null
        }

        val host = Esp32DiscoveryPacket.resolveTargetHost(
            payloadIp = json.optString(Esp32DiscoveryPacket.FIELD_IP),
            sourceHost = packet.address?.hostAddress.orEmpty()
        )
        if (host.isBlank()) {
            return null
        }

        val port = json.optInt(
            Esp32DiscoveryPacket.FIELD_UDP_PORT,
            BleProvisioningContract.DEFAULT_UDP_PORT
        )
        return DiscoveryResult(host, port)
    }

    private data class DiscoveryResult(
        val host: String,
        val port: Int
    )

    companion object {
        private const val BUFFER_SIZE = 512
        private const val RECEIVE_TIMEOUT_MS = 1_000
        private const val BROADCAST_ADDRESS = "255.255.255.255"
        private const val TAG = "Esp32DiscoveryClient"
    }
}
