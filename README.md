# Integrate Camect with home-assistant
======================================

## Configure
Please follow the following instructions:
- Copy file "camect-card.js" to $ha_config_dir/www.
- Copy folder "camect" to $ha_config_dir/custom_components.
- Add following to $ha_config_dir/configuration.yaml
<pre>
camect:
  - host: YOUR_CAMECT_HOME_LOCAL_IP
    port: 443
    username: admin
    password: admin_PASSWORD
    camera_ids: YOUR_CAMERA_IDS_SEPARATED_BY_COMMA
</pre>
- If you are using lovelace, put following into $ha_config_dir/ui-lovelace.yaml
<pre>
resources:
  - url: /local/camect-card.js
    type: module

views:
  - title: Camect
    cards:
      - type: "custom:camect-card"
        entity: camera.camect_YOUR_CAMERA_ID
</pre>
  If you don't have ui-lovelace.yaml yet, add the following into $ha_config_dir/configuration.yaml
<pre>
lovelace:
   mode: yaml
</pre>

## Listen to events
<pre>
hass.bus.listen('camect_event', lambda evt: print(evt))
</pre>
Sample event:
<pre>
type=alert
desc=Camera Driveway just saw a car.
url=https://home.camect.com/home/xxxxxxxx/camera?id=yyyyyyy&ts=1556228517560
</pre>
