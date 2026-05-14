package com.zoelowell.headunithudbridge

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.Build
import android.os.ParcelUuid
import java.util.UUID

class BleProvisioningClient(
    private val context: Context,
    private val listener: Listener
) {
    interface Listener {
        fun onProvisioningMessage(message: String)
        fun onProvisioningComplete(ipAddress: String, udpPort: Int)
        fun onProvisioningReadyForDiscovery(udpPort: Int)
    }

    private val bluetoothAdapter = context.getSystemService(BluetoothManager::class.java)?.adapter
    private val localizedContext = context.applicationContext.withHudLocale()
    private val serviceUuid = UUID.fromString(BleProvisioningContract.SERVICE_UUID)
    private val credentialsUuid = UUID.fromString(BleProvisioningContract.WIFI_CREDENTIALS_UUID)
    private val statusUuid = UUID.fromString(BleProvisioningContract.STATUS_UUID)
    private val clientConfigUuid = UUID.fromString(BleProvisioningContract.CLIENT_CHARACTERISTIC_CONFIG_UUID)

    private var bluetoothGatt: BluetoothGatt? = null
    private var pendingCredentials: WifiCredentialsPacket? = null
    private var credentialsWritten = false
    private var discoveryRequested = false
    private var statusReadRequested = false

    @SuppressLint("MissingPermission")
    fun provision(credentials: WifiCredentialsPacket) {
        val scanner = bluetoothAdapter?.bluetoothLeScanner
        if (bluetoothAdapter == null || scanner == null || bluetoothAdapter.isEnabled.not()) {
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_not_ready))
            return
        }

        pendingCredentials = credentials
        credentialsWritten = false
        discoveryRequested = false
        statusReadRequested = false
        listener.onProvisioningMessage(localizedContext.getString(R.string.ble_scanning, BleProvisioningContract.DEVICE_NAME))

        val filters = listOf(
            ScanFilter.Builder()
                .setServiceUuid(ParcelUuid(serviceUuid))
                .build()
        )
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        scanner.startScan(filters, settings, scanCallback)
    }

    @SuppressLint("MissingPermission")
    fun close() {
        bluetoothAdapter?.bluetoothLeScanner?.stopScan(scanCallback)
        bluetoothGatt?.close()
        bluetoothGatt = null
    }

    private val scanCallback = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val device = result.device ?: return
            bluetoothAdapter?.bluetoothLeScanner?.stopScan(this)
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_connecting, device.displayName()))
            bluetoothGatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
        }

        override fun onScanFailed(errorCode: Int) {
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_scan_failed, errorCode))
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_connection_failed, status))
                close()
                return
            }

            if (newState == BluetoothProfile.STATE_CONNECTED) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_connected_requesting_mtu))
                if (!gatt.requestMtu(REQUESTED_MTU)) {
                    gatt.discoverServices()
                }
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_disconnected))
                close()
            }
        }

        @SuppressLint("MissingPermission")
        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_mtu_set, mtu))
            gatt.discoverServices()
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status != BluetoothGatt.GATT_SUCCESS) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_service_discovery_failed, status))
                return
            }

            val service = gatt.getService(serviceUuid)
            if (service == null) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_service_missing))
                return
            }

            val statusCharacteristic = service.getCharacteristic(statusUuid)
            if (statusCharacteristic != null) {
                gatt.setCharacteristicNotification(statusCharacteristic, true)
                val descriptor = statusCharacteristic.getDescriptor(clientConfigUuid)
                if (descriptor != null && writeDescriptor(gatt, descriptor, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)) {
                    return
                }
            }

            writePendingCredentials(gatt)
        }

        override fun onDescriptorWrite(
            gatt: BluetoothGatt,
            descriptor: BluetoothGattDescriptor,
            status: Int
        ) {
            writePendingCredentials(gatt)
        }

        override fun onCharacteristicWrite(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int
        ) {
            if (characteristic.uuid == credentialsUuid) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    requestDiscovery()
                }
                listener.onProvisioningMessage(
                    if (status == BluetoothGatt.GATT_SUCCESS) {
                        localizedContext.getString(R.string.ble_wifi_sent_ready)
                    } else {
                        localizedContext.getString(R.string.ble_wifi_write_failed, status)
                    }
                )
            }
        }

        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray
        ) {
            handleStatus(gatt, value)
        }

        @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic
        ) {
            handleStatus(gatt, characteristic.value ?: return)
        }

        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray,
            status: Int
        ) {
            if (characteristic.uuid == statusUuid && status == BluetoothGatt.GATT_SUCCESS) {
                handleStatus(gatt, value, allowStatusReadRetry = false)
            }
        }

        @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
        override fun onCharacteristicRead(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            status: Int
        ) {
            if (characteristic.uuid == statusUuid && status == BluetoothGatt.GATT_SUCCESS) {
                handleStatus(gatt, characteristic.value ?: return, allowStatusReadRetry = false)
            }
        }
    }

    @SuppressLint("MissingPermission")
    private fun writePendingCredentials(gatt: BluetoothGatt) {
        if (credentialsWritten) return
        val payload = pendingCredentials?.toJson()?.toByteArray(Charsets.UTF_8) ?: return
        val characteristic = gatt.getService(serviceUuid)
            ?.getCharacteristic(credentialsUuid)

        if (characteristic == null) {
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_wifi_characteristic_missing))
            return
        }

        credentialsWritten = true
        characteristic.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
        val accepted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            gatt.writeCharacteristic(
                characteristic,
                payload,
                BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            ) == BluetoothGatt.GATT_SUCCESS
        } else {
            @Suppress("DEPRECATION")
            characteristic.value = payload
            @Suppress("DEPRECATION")
            gatt.writeCharacteristic(characteristic)
        }

        if (!accepted) {
            listener.onProvisioningMessage(localizedContext.getString(R.string.ble_wifi_write_rejected))
        }
    }

    @SuppressLint("MissingPermission")
    private fun writeDescriptor(
        gatt: BluetoothGatt,
        descriptor: BluetoothGattDescriptor,
        value: ByteArray
    ): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            gatt.writeDescriptor(descriptor, value) == BluetoothGatt.GATT_SUCCESS
        } else {
            @Suppress("DEPRECATION")
            descriptor.value = value
            @Suppress("DEPRECATION")
            gatt.writeDescriptor(descriptor)
        }
    }

    @SuppressLint("MissingPermission")
    private fun handleStatus(
        gatt: BluetoothGatt,
        value: ByteArray,
        allowStatusReadRetry: Boolean = true
    ) {
        val body = value.toString(Charsets.UTF_8)
        val status = BleStatusPacket.parse(body)
        if (status == null) {
            if (body.startsWith("""{"state":"connected"""")) {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_compact_status_received))
                requestDiscovery()
            } else {
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_status_parse_failed, body))
            }
            return
        }

        listener.onProvisioningMessage(localizedContext.getString(R.string.ble_status_format, status.state, status.message))

        if (status.state == BleProvisioningContract.STATE_CONNECTED) {
            if (status.ipAddress.isNotBlank()) {
                listener.onProvisioningComplete(
                    status.ipAddress,
                    pendingCredentials?.udpPort ?: BleProvisioningContract.DEFAULT_UDP_PORT
                )
                return
            }
            if (allowStatusReadRetry && !statusReadRequested) {
                statusReadRequested = true
                listener.onProvisioningMessage(localizedContext.getString(R.string.ble_wifi_connected_checking_ip))
                if (readStatusCharacteristic(gatt)) {
                    return
                }
            }
            requestDiscovery()
        }
    }

    @SuppressLint("MissingPermission")
    private fun readStatusCharacteristic(gatt: BluetoothGatt): Boolean {
        val characteristic = gatt.getService(serviceUuid)
            ?.getCharacteristic(statusUuid)
            ?: return false
        return gatt.readCharacteristic(characteristic)
    }

    private fun requestDiscovery() {
        if (discoveryRequested) {
            return
        }
        discoveryRequested = true
        listener.onProvisioningReadyForDiscovery(pendingCredentials?.udpPort ?: BleProvisioningContract.DEFAULT_UDP_PORT)
    }

    @SuppressLint("MissingPermission")
    private fun BluetoothDevice.displayName(): String {
        return name ?: address ?: BleProvisioningContract.DEVICE_NAME
    }

    companion object {
        private const val REQUESTED_MTU = 185
    }
}
