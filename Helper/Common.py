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
    return int(t[0]), int(t[1])
