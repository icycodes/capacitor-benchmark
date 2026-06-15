package com.example.myapp;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "DeviceSensor")
public class DeviceSensorPlugin extends Plugin {

    private static final java.util.Set<String> SUPPORTED_SENSORS = new java.util.HashSet<>(
            java.util.Arrays.asList("temperature", "humidity", "battery")
    );

    @PluginMethod
    public void getReading(PluginCall call) {
        String sensor = call.getString("sensor");
        if (sensor == null || sensor.isEmpty()) {
            call.reject("Missing required parameter: sensor");
            return;
        }

        JSObject result = new JSObject();
        switch (sensor) {
            case "temperature":
                result.put("sensor", "temperature");
                result.put("value", 22.5);
                result.put("unit", "C");
                call.resolve(result);
                break;
            case "humidity":
                result.put("sensor", "humidity");
                result.put("value", 65.0);
                result.put("unit", "%");
                call.resolve(result);
                break;
            case "battery":
                result.put("sensor", "battery");
                result.put("value", 87.0);
                result.put("unit", "%");
                call.resolve(result);
                break;
            default:
                call.reject("Unknown sensor: " + sensor);
                break;
        }
    }

    @PluginMethod
    public void isAvailable(PluginCall call) {
        String sensor = call.getString("sensor");
        JSObject result = new JSObject();
        if (sensor != null && SUPPORTED_SENSORS.contains(sensor)) {
            result.put("available", true);
        } else {
            result.put("available", false);
        }
        call.resolve(result);
    }
}
