import subprocess


def check_device(out):
    s = out.replace("List of devices attached", "").replace("\t", "").replace("\r", "").replace("\n", "").replace(
        "device", "")
    if not s or "." in s:
        return False
    else:
        return True


def get_android_display_info(out):
    s = out[out.find("init="):]
    t = s[s.find("="):s.find(" ")].replace("=", "").split("x")
    print(t)
    return int(t[0]), int(t[1])


def check_adb_keyboard_installed():
    p = subprocess.Popen("adb shell ime list -s", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate(timeout=10)[0].decode()
    if "com.android.adbkeyboard/.AdbIME" not in out:
        return False
    else:
        return True


def set_current_input_method():
    p = subprocess.Popen("adb shell ime set com.android.adbkeyboard/.AdbIME", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate(timeout=10)[0].decode()
    if "Input method com.android.adbkeyboard/.AdbIME selected" not in out:
        return False
    else:
        return True
