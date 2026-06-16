package com.example.myapp;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "Counter")
public class CounterPlugin extends Plugin {

    private int counter = 0;

    @PluginMethod
    public void increment(PluginCall call) {
        counter += 1;
        JSObject data = new JSObject();
        data.put("value", counter);
        notifyListeners("change", data);
        call.resolve(data);
    }

    @PluginMethod
    public void reset(PluginCall call) {
        counter = 0;
        JSObject data = new JSObject();
        data.put("value", counter);
        notifyListeners("change", data);
        call.resolve(data);
    }

    @PluginMethod
    public void getValue(PluginCall call) {
        JSObject data = new JSObject();
        data.put("value", counter);
        call.resolve(data);
    }
}
