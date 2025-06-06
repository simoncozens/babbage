import shutil
import subprocess
import numpy as np
from PIL import Image, ImageEnhance
from selenium import webdriver
from chromedriver_py import binary_path
import tempfile
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")

DIDDER_GLOBAL_ARGS = [
    "--strength",
    "50%",
    "--width",
    "800",
    "--height",
    "480",
    "--palette",
    "black white",
    "-g",
]


def set_viewport_size(driver, width, height):
    window_size = driver.execute_script(
        """
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """,
        width,
        height,
    )
    driver.set_window_size(*window_size)


def render_html(html):
    svc = webdriver.ChromeService(executable_path=binary_path)
    driver = webdriver.Chrome(service=svc, options=options)
    set_viewport_size(driver, 800, 480)
    with tempfile.NamedTemporaryFile(suffix=".html") as temp_file:
        path = temp_file.name
        temp_file.write(html.encode("utf-8"))
        temp_file.flush()
        driver.get("file://" + path)

        with tempfile.NamedTemporaryFile(suffix=".png") as temp_file:
            path = temp_file.name
            driver.save_screenshot(path)
            with Image.open(path) as img:
                img = greyify(img)

    driver.quit()
    return img


def greyify(img):
    # If we have didder, use it.
    if shutil.which("didder") is not None:

        with tempfile.NamedTemporaryFile(suffix=".png") as temp_file:
            path = temp_file.name
            img.save(path)
            subprocess.run(
                [
                    "didder",
                ]
                + DIDDER_GLOBAL_ARGS
                + [
                    "-i",
                    path,
                    "-o",
                    path,
                    "--contrast",
                    "0.3",
                    "edm",
                    "--serpentine",
                    "FloydSteinberg",
                ]
            )
            return Image.open(path).convert("1")

    img = img.resize((800, 480))
    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    img = np_to_pil(floyd_steinberg(pil_to_np(img)))
    img = img.convert("1")
    return img


def floyd_steinberg(image):
    h, w = image.shape
    for y in range(h):
        for x in range(w):
            old = image[y, x]
            new = np.round(old)
            image[y, x] = new
            error = old - new
            if x + 1 < w:
                image[y, x + 1] += error * 0.4375  # right, 7 / 16
            if (y + 1 < h) and (x + 1 < w):
                image[y + 1, x + 1] += error * 0.0625  # right, down, 1 / 16
            if y + 1 < h:
                image[y + 1, x] += error * 0.3125  # down, 5 / 16
            if (x - 1 >= 0) and (y + 1 < h):
                image[y + 1, x - 1] += error * 0.1875  # left, down, 3 / 16
    return image


def pil_to_np(pilimage):
    return np.array(pilimage) / 255


def np_to_pil(image):
    return Image.fromarray((image * 255).astype("uint8"))
