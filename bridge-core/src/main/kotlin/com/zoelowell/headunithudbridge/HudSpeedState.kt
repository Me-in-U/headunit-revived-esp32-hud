package com.zoelowell.headunithudbridge

class HudSpeedState {
    private var latestPacket: HudSpeedPacket = HudSpeedPacket.unknown()

    fun update(packet: HudSpeedPacket) {
        latestPacket = packet
    }

    fun currentPacket(): HudSpeedPacket = latestPacket
}