package com.example.myapp;

import android.graphics.Color;

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
            call.reject("A color string in #RRGGBB format is required");
            return;
        }

        try {
            final int parsedColor = Color.parseColor(color);
            getActivity().runOnUiThread(() -> {
                getActivity().getWindow().setNavigationBarColor(parsedColor);
            });
            call.resolve();
        } catch (IllegalArgumentException e) {
            call.reject("Invalid color format. Expected #RRGGBB, got: " + color);
        }
    }
}
