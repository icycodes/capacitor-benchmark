package com.example.myapp;

import android.graphics.Color;
import android.view.Window;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "NavBar")
public class NavBarPlugin extends Plugin {

    @PluginMethod
    public void setColor(PluginCall call) {
        String colorStr = call.getString("color");
        if (colorStr == null) {
            call.reject("Must provide a color");
            return;
        }

        try {
            final int color = Color.parseColor(colorStr);
            getActivity().runOnUiThread(() -> {
                Window window = getActivity().getWindow();
                window.setNavigationBarColor(color);
                call.resolve();
            });
        } catch (IllegalArgumentException ex) {
            call.reject("Invalid color provided", ex);
        }
    }
}
