package com.example.myapp;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "DeviceSensor")
public class DeviceSensorPlugin extends Plugin {

    private static final String[] SUPPORTED_SENSORS = {"temperature", "humidity", "battery"};

    private boolean isSupported(String sensor) {
        for (String s : SUPPORTED_SENSORS) {
            if (s.equals(sensor)) {
                return true;
            }
        }
        return false;
    }

    @PluginMethod
    public void getReading(PluginCall call) {
        String sensor = call.getString("sensor");

        if (sensor == null || !isSupported(sensor)) {
            call.reject("Unsupported sensor: " + sensor);
            return;
        }

        JSObject result = new JSObject();

        switch (sensor) {
            case "temperature":
                result.put("sensor", "temperature");
                result.put("value", 22.5);
                result.put("unit", "C");
                break;
            case "humidity":
                result.put("sensor", "humidity");
                result.put("value", 65.0);
                result.put("unit", "%");
                break;
            case "battery":
                result.put("sensor", "battery");
                result.put("value", 87.0);
                result.put("unit", "%");
                break;
            default:
                call.reject("Unsupported sensor: " + sensor);
                return;
        }

        call.resolve(result);
    }

    @PluginMethod
    public void isAvailable(PluginCall call) {
        String sensor = call.getString("sensor");

        JSObject result = new JSObject();

        if (sensor != null && isSupported(sensor)) {
            result.put("available", true);
        } else {
            result.put("available", false);
        }

        call.resolve(result);
    }
}
