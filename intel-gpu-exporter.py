from prometheus_client import start_http_server, Gauge
import os
import sys
import subprocess
import json
import logging

igpu_engines_blitter_0_busy = Gauge(
    "igpu_engines_blitter_0_busy", "Blitter 0 busy utilisation %"
)
igpu_engines_blitter_0_sema = Gauge(
    "igpu_engines_blitter_0_sema", "Blitter 0 sema utilisation %"
)
igpu_engines_blitter_0_wait = Gauge(
    "igpu_engines_blitter_0_wait", "Blitter 0 wait utilisation %"
)

igpu_engines_render_3d_0_busy = Gauge(
    "igpu_engines_render_3d_0_busy", "Render 3D 0 busy utilisation %"
)
igpu_engines_render_3d_0_sema = Gauge(
    "igpu_engines_render_3d_0_sema", "Render 3D 0 sema utilisation %"
)
igpu_engines_render_3d_0_wait = Gauge(
    "igpu_engines_render_3d_0_wait", "Render 3D 0 wait utilisation %"
)

igpu_engines_video_0_busy = Gauge(
    "igpu_engines_video_0_busy", "Video 0 busy utilisation %"
)
igpu_engines_video_0_sema = Gauge(
    "igpu_engines_video_0_sema", "Video 0 sema utilisation %"
)
igpu_engines_video_0_wait = Gauge(
    "igpu_engines_video_0_wait", "Video 0 wait utilisation %"
)

igpu_engines_video_enhance_0_busy = Gauge(
    "igpu_engines_video_enhance_0_busy", "Video Enhance 0 busy utilisation %"
)
igpu_engines_video_enhance_0_sema = Gauge(
    "igpu_engines_video_enhance_0_sema", "Video Enhance 0 sema utilisation %"
)
igpu_engines_video_enhance_0_wait = Gauge(
    "igpu_engines_video_enhance_0_wait", "Video Enhance 0 wait utilisation %"
)

igpu_frequency_actual = Gauge("igpu_frequency_actual", "Frequency actual MHz")
igpu_frequency_requested = Gauge("igpu_frequency_requested", "Frequency requested MHz")

igpu_imc_bandwidth_reads = Gauge("igpu_imc_bandwidth_reads", "IMC reads MiB/s")
igpu_imc_bandwidth_writes = Gauge("igpu_imc_bandwidth_writes", "IMC writes MiB/s")

igpu_interrupts = Gauge("igpu_interrupts", "Interrupts/s")

igpu_period = Gauge("igpu_period", "Period ms")

igpu_power_gpu = Gauge("igpu_power_gpu", "GPU power W")
igpu_power_package = Gauge("igpu_power_package", "Package power W")

igpu_rc6 = Gauge("igpu_rc6", "RC6 %")


def update(data):
    igpu_engines_blitter_0_busy.set(
        data.get("engines", {}).get("Blitter/0", {}).get("busy", 0.0)
    )
    igpu_engines_blitter_0_sema.set(
        data.get("engines", {}).get("Blitter/0", {}).get("sema", 0.0)
    )
    igpu_engines_blitter_0_wait.set(
        data.get("engines", {}).get("Blitter/0", {}).get("wait", 0.0)
    )

    igpu_engines_render_3d_0_busy.set(
        data.get("engines", {}).get("Render/3D/0", {}).get("busy", 0.0)
    )
    igpu_engines_render_3d_0_sema.set(
        data.get("engines", {}).get("Render/3D/0", {}).get("sema", 0.0)
    )
    igpu_engines_render_3d_0_wait.set(
        data.get("engines", {}).get("Render/3D/0", {}).get("wait", 0.0)
    )

    igpu_engines_video_0_busy.set(
        data.get("engines", {}).get("Video/0", {}).get("busy", 0.0)
    )
    igpu_engines_video_0_sema.set(
        data.get("engines", {}).get("Video/0", {}).get("sema", 0.0)
    )
    igpu_engines_video_0_wait.set(
        data.get("engines", {}).get("Video/0", {}).get("wait", 0.0)
    )

    igpu_engines_video_enhance_0_busy.set(
        data.get("engines", {}).get("VideoEnhance/0", {}).get("busy", 0.0)
    )
    igpu_engines_video_enhance_0_sema.set(
        data.get("engines", {}).get("VideoEnhance/0", {}).get("sema", 0.0)
    )
    igpu_engines_video_enhance_0_wait.set(
        data.get("engines", {}).get("VideoEnhance/0", {}).get("wait", 0.0)
    )

    igpu_frequency_actual.set(data.get("frequency", {}).get("actual", 0))
    igpu_frequency_requested.set(data.get("frequency", {}).get("requested", 0))

    igpu_imc_bandwidth_reads.set(data.get("imc-bandwidth", {}).get("reads", 0))
    igpu_imc_bandwidth_writes.set(data.get("imc-bandwidth", {}).get("writes", 0))

    igpu_interrupts.set(data.get("interrupts", {}).get("count", 0))

    igpu_period.set(data.get("period", {}).get("duration", 0))

    igpu_power_gpu.set(data.get("power", {}).get("GPU", 0))
    igpu_power_package.set(data.get("power", {}).get("Package", 0))

    igpu_rc6.set(data.get("rc6", {}).get("value", 0))


if __name__ == "__main__":
    # Environment variables
    port = os.getenv("PORT", 8080)
    period = os.getenv("REFRESH_PERIOD_MS", 10000)
    device = os.getenv("DEVICE")
    debug = os.getenv("DEBUG", False)

    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG if debug else logging.INFO)

    start_http_server(port)

    if device is not None:
        cmd = "intel_gpu_top -J -p -s {} -d {}".format(int(period), device)
    else:
        cmd = "intel_gpu_top -J -p -s {}".format(int(period))

    process = subprocess.Popen(
        cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    logging.info("Started " + cmd)
    output = ""
    first_object = True  # Track if we need to skip opening bracket

    if os.getenv("IS_DOCKER", True):
        for line in process.stdout:
            line = line.decode("utf-8").strip()
            output += line
            
            # Skip initial opening bracket
            if first_object and output.startswith("["):
                output = output[1:]
                first_object = False
            
            # Try to find complete JSON objects
            # Look for closing } that completes an object
            if output.count("{") > 0 and output.count("{") == output.count("}"):
                try:
                    # Remove any trailing comma
                    data_str = output.strip().rstrip(",")
                    logging.debug(f"Attempting to parse: {data_str}")
                    data = json.loads(data_str)
                    logging.debug(f"Parsed data: {data}")
                    update(data)
                    output = ""  # Reset for next object
                except json.JSONDecodeError as ex:
                    logging.debug(f"JSON decode error: {ex}")
                    continue

    else:
        raise Exception("Not in Docker, the functionality is not yet implemented for this mode.")
