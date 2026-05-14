package com.zoelowell.headunithudbridge

data class BleStatusPacket(
    val state: String,
    val ipAddress: String,
    val message: String
) {
    companion object {
        fun parse(json: String): BleStatusPacket? {
            val body = json.trim()
            if (!body.startsWith("{") || !body.endsWith("}")) {
                return null
            }

            val compactState = body.extractJsonString(BleProvisioningContract.FIELD_COMPACT_STATE)
            val state = compactState?.toVerboseState()
                ?: body.extractJsonString(BleProvisioningContract.FIELD_STATE)
                ?: return null
            val ip = body.extractJsonString(BleProvisioningContract.FIELD_COMPACT_IP)
                ?: body.extractJsonString(BleProvisioningContract.FIELD_IP)
                ?: ""
            val message = body.extractJsonString(BleProvisioningContract.FIELD_COMPACT_MESSAGE)
                ?: body.extractJsonString(BleProvisioningContract.FIELD_MESSAGE)
                ?: state

            return BleStatusPacket(
                state = state,
                ipAddress = ip,
                message = message
            )
        }

        private fun String.extractJsonString(field: String): String? {
            val pattern = Regex(""""${Regex.escape(field)}"\s*:\s*"((?:\\.|[^"])*)"""")
            return pattern.find(this)?.groupValues?.get(1)?.unescapeJsonString()
        }

        private fun String.toVerboseState(): String {
            return when (this) {
                BleProvisioningContract.COMPACT_STATE_IDLE -> BleProvisioningContract.STATE_IDLE
                BleProvisioningContract.COMPACT_STATE_CONNECTING -> BleProvisioningContract.STATE_CONNECTING
                BleProvisioningContract.COMPACT_STATE_CONNECTED -> BleProvisioningContract.STATE_CONNECTED
                BleProvisioningContract.COMPACT_STATE_FAILED -> BleProvisioningContract.STATE_FAILED
                else -> this
            }
        }

        private fun String.unescapeJsonString(): String {
            return replace("\\\"", "\"")
                .replace("\\\\", "\\")
        }
    }
}