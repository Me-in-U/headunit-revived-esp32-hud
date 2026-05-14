package com.zoelowell.headunithudbridge

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

data class UdpHudSendResult(
    val targetHost: String,
    val targetPort: Int,
    val errorMessage: String?
) {
    val sent: Boolean
        get() = errorMessage == null
}

class UdpHudSender(
    private val host: String,
    private val port: Int
) {
    fun send(payload: String): UdpHudSendResult {
        val result = sendFireAndForget(payload)
        if (result.errorMessage != null) {
            throw IllegalStateException(result.errorMessage)
        }
        return result
    }

    fun sendFireAndForget(payload: String): UdpHudSendResult {
        val bytes = payload.toByteArray(Charsets.UTF_8)
        val packet = DatagramPacket(bytes, bytes.size, InetAddress.getByName(host), port)
        return try {
            DatagramSocket().use { socket ->
                socket.broadcast = true
                socket.send(packet)
            }
            UdpHudSendResult(host, port, errorMessage = null)
        } catch (error: Exception) {
            UdpHudSendResult(host, port, errorMessage = error.message ?: error.javaClass.simpleName)
        }
    }
}