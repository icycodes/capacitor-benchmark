package com.example.myapp;

import android.graphics.Color;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "NavBar")
public class NavBarPlugin extends Plugin {

    @PluginMethod
    public void setColor(final PluginCall call) {
        final String color = call.getString("color");
        if (color == null) {
            call.reject("Color is required");
            return;
        }

        getActivity().runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    getActivity().getWindow().setNavigationBarColor(Color.parseColor(color));
                    call.resolve();
                } catch (Exception e) {
                    call.reject("Failed to set navigation bar color: " + e.getMessage());
                }
            }
        });
    }
}
