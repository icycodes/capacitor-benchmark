package com.example.myapp;

import android.graphics.Color;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "NavBar")
public class NavBarPlugin extends Plugin {

    @PluginMethod
    public void setColor(PluginCall call) {
        String color = call.getString("color");
        if (color == null || color.isEmpty()) {
            call.reject("color must be provided");
            return;
        }
        try {
            int parsedColor = Color.parseColor(color);
            getActivity().runOnUiThread(() -> {
                getActivity().getWindow().setNavigationBarColor(parsedColor);
            });
            call.resolve(new JSObject());
        } catch (IllegalArgumentException e) {
            call.reject("Invalid color format: " + color);
        }
    }
}