package com.zoelowell.headunithudbridge

data class WifiCredentialsPacket(
    val ssid: String,
    val password: String,
    val udpPort: Int = BleProvisioningContract.DEFAULT_UDP_PORT
) {
    fun toJson(): String = buildString {
        append('{')
        appendJsonField(BleProvisioningContract.FIELD_SSID, ssid)
        append(',')
        appendJsonField(BleProvisioningContract.FIELD_PASSWORD, password)
        append(',')
        append("\"")
        append(BleProvisioningContract.FIELD_UDP_PORT)
        append("\":")
        append(udpPort)
        append('}')
    }

    private fun StringBuilder.appendJsonField(name: String, value: String) {
        append('"')
        append(name)
        append("\":\"")
        append(value.escapeJsonString())
        append('"')
    }

    private fun String.escapeJsonString(): String = buildString {
        for (char in this@escapeJsonString) {
            when (char) {
                '\\' -> append("\\\\")
                '"' -> append("\\\"")
                '\b' -> append("\\b")
                '\u000C' -> append("\\f")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> {
                    if (char < ' ') {
                        append("\\u")
                        append(char.code.toString(16).padStart(4, '0'))
                    } else {
                        append(char)
                    }
                }
            }
        }
    }
}