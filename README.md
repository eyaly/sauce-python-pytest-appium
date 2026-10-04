# PawKnits: Python + Appium on Sauce Labs Real Devices

A demo test framework that runs **Python + Appium** tests for the PawKnits Android app
on **Sauce Labs real devices**, in parallel across several phones, using **pytest** and
the **Page Object** pattern. It is built to run locally and in **Azure DevOps**.

```
21 tests = 7 test cases × 3 Android devices, run in parallel (~3 minutes)
```

---

## How the pieces fit together

```
┌──────────────────────────────────────────────────┐
│ pytest              runs the tests, reports      │  test runner
│   ├─ fixtures       open/close a device session  │  (conftest.py)
│   └─ pytest-xdist   runs tests in parallel       │
├──────────────────────────────────────────────────┤
│ Page Objects        one class per app screen     │  pages/
├──────────────────────────────────────────────────┤
│ Appium-Python-Client  sends commands over HTTP   │  client library
├──────────────────────────────────────────────────┤
│ Appium server on Sauce Labs (EU data center)     │  hosted by Sauce
├──────────────────────────────────────────────────┤
│ Real Android phones (Pixel, Samsung, ...)        │
└──────────────────────────────────────────────────┘
```

| Piece | What it does |
|---|---|
| **Appium** | Controls the phone: taps, types, swipes. Sauce Labs hosts the server. |
| **Appium-Python-Client** | The Python library that talks to Appium (`driver.find_element(...).click()`). |
| **pytest** | Finds `test_*` functions, runs them, reports pass/fail, writes JUnit XML. |
| **Fixture** | pytest's setup/teardown mechanism. The `driver` fixture opens a Sauce session before each test and closes it afterwards, even if the test fails. |
| **pytest-xdist** | Runs tests in parallel: `-n 6` means 6 device sessions at the same time. |
| **Page Object** | A class per screen that hides locators, so tests read like user actions. |

---

## The app under test

**PawKnits**, a dog-sweater shop (Kotlin + Jetpack Compose).
Flow: **Login → Shop → Cart → Checkout → Order confirmation**.

| | |
|---|---|
| APK in this repo | `Apps/PawKnits.apk` |
| Sauce storage file | `PawKnits.apk` (in the **EU** data center) |
| Package | `com.pawknits.demo` |
| Valid user | `doglover` / `woof1234` |
| Locked user | `locked` / `woof1234` |
| Approved card | `4242 4242 4242 4242` (prefilled) |
| Declined card | `4000 0000 0000 0002` |

### Uploading the app to Sauce Labs storage

The tests don't send the APK. Each session installs it from **Sauce Labs app storage**,
through this capability in `config/capabilities.py`:

```python
"appium:app": "storage:filename=PawKnits.apk",
```

So the APK must be in storage **before** you run the tests. You only need to upload it
again when the app changes.

**Upload with the Sauce Labs REST API.** Use the **EU** endpoint, because app storage is
separate per data center and the tests run in EU:

```bash
curl -u "$SAUCE_USERNAME:$SAUCE_ACCESS_KEY" -X POST \
  "https://api.eu-central-1.saucelabs.com/v1/storage/upload" \
  -F "payload=@Apps/PawKnits.apk" \
  -F "name=PawKnits.apk"
```

| Part | Meaning |
|---|---|
| `-u "$SAUCE_USERNAME:$SAUCE_ACCESS_KEY"` | Authenticates with your Sauce Labs credentials |
| `api.eu-central-1.saucelabs.com` | The EU data center's API |
| `payload=@Apps/PawKnits.apk` | The local file to upload (`@` means "read this file") |
| `name=PawKnits.apk` | The file name in storage, which `storage:filename=` refers to |

The response is JSON describing the uploaded file, including its `id`. Uploading again
with the same `name` doesn't overwrite the old file: it adds a new version, and
`storage:filename=PawKnits.apk` always uses the **most recent** upload.

**Check that it's there:**

```bash
curl -u "$SAUCE_USERNAME:$SAUCE_ACCESS_KEY" \
  "https://api.eu-central-1.saucelabs.com/v1/storage/files?q=PawKnits.apk"
```

You can also see it in the Sauce Labs UI under **App Management**, or upload it there by
drag and drop instead of using the API. Make sure the UI is set to the EU data center.

---

## Project structure

```
sauce-python-pytest-appium/
├── conftest.py              # pytest wiring: device parametrization, driver fixture, Sauce result
├── pytest.ini               # pytest settings (JUnit report, markers)
├── requirements.txt
├── Apps/
│   └── PawKnits.apk         # the app under test (upload it to Sauce storage, see above)
├── config/
│   ├── settings.py          # credentials, Sauce EU URL, build name
│   ├── capabilities.py      # hardcoded Appium capabilities per device  ← edit to change devices
│   └── test_data.py         # users, cards, products
├── pages/                   # Page Objects
│   ├── base_page.py         # shared helpers: find, tap, type, wait, scroll
│   ├── login_page.py
│   ├── shop_page.py
│   ├── cart_page.py
│   ├── checkout_page.py
│   └── order_complete_page.py
└── tests/
    ├── test_login.py        # valid login, locked user, wrong password
    ├── test_cart.py         # add items + badge + total, quantity +/- and remove
    └── test_checkout.py     # successful order, declined card
```

---

## Setup

Requires **Python 3.10+**.

**First time** (or when the `.venv` folder doesn't exist), create a virtual environment and
install the packages:

```bash
git clone https://github.com/eyaly/sauce-python-pytest-appium.git
cd sauce-python-pytest-appium
python3 -m venv .venv                # create the virtual environment
source .venv/bin/activate            # activate it. Windows: .venv\Scripts\activate
pip install -r requirements.txt      # install pytest, Appium client, xdist, ...
```

**Every new terminal** (when `.venv` already exists): activate it again. Activation only
lasts for the terminal it was run in.

```bash
cd sauce-python-pytest-appium
source .venv/bin/activate
```

When it's active, the prompt starts with `(.venv)`. VS Code and PyCharm usually activate it
automatically in their built-in terminals. To check:

```bash
ls .venv          # "No such file or directory" → do the first-time steps above
which pytest      # a path ending in .venv/bin/pytest → ready to run
```

You can also skip activation and call the venv's pytest directly: `.venv/bin/pytest ...`.
Type `deactivate` to leave the virtual environment.

Set your Sauce Labs credentials (from *Account → User settings* in Sauce Labs):

```bash
export SAUCE_USERNAME="your-username"
export SAUCE_ACCESS_KEY="your-access-key"
```

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SAUCE_USERNAME` / `SAUCE_ACCESS_KEY` | (required) | Sauce Labs credentials |
| `SAUCE_BUILD_NAME` | auto | Groups the run in the Sauce UI. Auto: Azure build number, or a timestamp locally |
| `DEVICES` | all | Same as `--devices` |
| `ELEMENT_TIMEOUT` | `20` | Seconds to wait for an element |

> The tests run in the Sauce Labs **EU data center** (`eu-central-1`), set in
> `config/settings.py`. The APK must be uploaded to EU storage, because app storage
> is separate per data center.

---

## Running the tests

### How many tests run

**Every selected test runs once on every selected device.** Each run is its own Sauce
Labs session, on its own phone.

```
test runs = test cases × devices
```

The suite has **7 test cases** (3 login, 2 cart, 2 checkout) and **3 devices**
(`pixel`, `samsung`, `android-14`). Three options control a run:

| Option | Controls | Default |
|---|---|---|
| file path / `-m` / `::test_name` | **which test cases** | all 7 |
| `--devices` | **which devices** each test case runs on | all 3 |
| `-n` | **how many run at the same time** (parallel sessions) | 1, one after another |

`-n` doesn't change *what* runs, only how fast. 14 test runs with `-n 6` means 6 run at
once, and the next one starts whenever one finishes.

### Examples

| Command | Test cases | Devices | Test runs | At once |
|---|---|---|---|---|
| `pytest -n 6` | all 7 | all 3 | **21** | 6 |
| `pytest` | all 7 | all 3 | **21** | 1 |
| `pytest -n 6 --devices pixel,samsung` | all 7 | pixel, samsung | **14** | 6 |
| `pytest -n 3 --devices pixel` | all 7 | pixel | **7** | 3 |
| `pytest -n 3 -m smoke` | 2 smoke tests | all 3 | **6** | 3 |
| `pytest tests/test_checkout.py -n 3` | 2 checkout tests | all 3 | **6** | 3 |
| `pytest tests/test_login.py --devices pixel` | 3 login tests | pixel | **3** | 1 |
| `pytest "tests/test_login.py::test_valid_user_can_log_in[samsung]"` | 1 | samsung | **1** | 1 |

For example, `pytest -n 6 --devices pixel,samsung` runs each of the 7 test cases once on
a Google phone (Android 17) and once on a Samsung phone (Android 16):

```
test_valid_user_can_log_in[pixel]        test_valid_user_can_log_in[samsung]
test_locked_out_user_sees_error[pixel]   test_locked_out_user_sees_error[samsung]
...                                      ...                     → 14 test runs
```

**Other useful options:**

```bash
pytest -n 6 --reruns 1             # retry a failed test once (real devices can be flaky)
pytest -n 6 -v                     # show each test's result and which worker ran it
pytest --collect-only -q           # list the test runs without running anything
pytest --devices pixel,samsung --collect-only -q   # preview the 14 runs above
```

Set `-n` to no more than your Sauce Labs **real-device concurrency**. Extra sessions
wait in the queue.

> All commands assume the virtual environment is active (`source .venv/bin/activate`).
> Without activating it, call pytest from the venv directly: `.venv/bin/pytest ...`

### Run one test file on one device

Give the file path and one device id with `--devices`:

```bash
pytest tests/test_login.py --devices pixel
```

This runs the 3 login tests one after another on a single Pixel phone. Variations:

```bash
pytest tests/test_login.py --devices samsung -v       # another device, show each test result
pytest tests/test_login.py --devices pixel -n 3       # the 3 tests in parallel (3 Pixel sessions)
pytest tests/test_login.py::test_valid_user_can_log_in --devices pixel   # one test only
pytest tests/test_login.py --devices pixel --collect-only -q             # preview, don't run
DEVICES=pixel pytest tests/test_login.py              # same, using the environment variable
```

Device ids are the keys in `config/capabilities.py`:

| id | `appium:deviceName` | `appium:platformVersion` | Runs on |
|---|---|---|---|
| `pixel` | `Google.*` | `17` | any Google phone with Android 17 |
| `samsung` | `Samsung.*` | `16` | any Samsung phone with Android 16 |
| `android-14` | `.*` | `14` | any phone with Android 14 |

### The capabilities

Each device is a hardcoded capabilities dictionary in `config/capabilities.py`,
the same JSON you would paste into Appium Inspector:

```python
CAPABILITIES = {
    "pixel": {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "Google.*",
        "appium:platformVersion": "17",
        "appium:app": "storage:filename=PawKnits.apk",
        "sauce:options": {
            "appiumVersion": "latest",
            "phoneOnly": True,
            "tags": ["python", "pytest", "pawknits"],
        },
    },
    "samsung": { ... },
    "android-14": { ... },
}
```

The `driver` fixture in `conftest.py` adds only the values that change per run to
`sauce:options`:

| Added at runtime | Value |
|---|---|
| `username`, `accessKey` | from `SAUCE_USERNAME` / `SAUCE_ACCESS_KEY`. Never hardcode credentials |
| `build` | `SAUCE_BUILD_NAME`, the Azure build number, or a local timestamp |
| `name` | the test function name, e.g. `test_valid_user_can_log_in` |

So the session Sauce receives for `test_valid_user_can_log_in` on `pixel` is:

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "Google.*",
  "appium:platformVersion": "17",
  "appium:app": "storage:filename=PawKnits.apk",
  "sauce:options": {
    "appiumVersion": "latest",
    "phoneOnly": true,
    "tags": ["python", "pytest", "pawknits"],
    "username": "...",
    "accessKey": "...",
    "build": "PawKnits Python - local - 2026-10-02 17:30:00",
    "name": "test_valid_user_can_log_in"
  }
}
```

The same test on different devices has the same job name in Sauce. You can tell them
apart in the dashboard by the device and OS columns.

### Choosing devices with regular expressions

On Sauce Labs real devices, `appium:deviceName` is a **regular expression** (*dynamic
allocation*): Sauce gives you any free phone whose name matches, ignoring case.
A broad pattern starts faster and fails less often, because more phones qualify.

| `appium:deviceName` | Matches |
|---|---|
| `Samsung.*` | any Samsung |
| `Samsung Galaxy S2[34].*` | Galaxy S23 / S24 models (incl. Plus, Ultra) |
| `Google Pixel [89].*` | Pixel 8 and 9 models |
| `(Samsung\|Google).*` | any Samsung or Google phone |
| `.*` | any phone (narrow it with `appium:platformVersion`) |
| `Google Pixel 8` | exactly that model (no regex, slower to get) |

To add a device, copy an entry in `config/capabilities.py` and give it a new key:

```python
    "galaxy-s": {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "Samsung Galaxy S.*",
        "appium:platformVersion": "15",
        "appium:app": "storage:filename=PawKnits.apk",
        "sauce:options": {
            "appiumVersion": "latest",
            "phoneOnly": True,
            "tags": ["python", "pytest", "pawknits"],
        },
    },
```

```bash
pytest tests/test_login.py --devices galaxy-s
```

`phoneOnly: true` stops broad patterns from picking a tablet. Check that the
pattern + version combination exists in the EU device pool (Sauce UI → *Live → Mobile App*),
or the session waits and then fails with "no device available".

### Results

- **Console**: pass/fail per test and device.
- **Sauce Labs**: each test is a job with video, screenshots, Appium logs and device logs,
  grouped under one build. Each test is marked passed or failed in Sauce. The job link is
  logged per test and stored in the JUnit report.
- **`reports/junit.xml`**: JUnit report (read by Azure DevOps).
- **`reports/failures/`**: screenshot (`.png`) and UI tree (`.xml`) of the screen
  where a test failed.

---

## How it works

### 1. Running on several devices in parallel

`config/capabilities.py` has one capabilities dictionary per device (`pixel`, `samsung`,
`android-14`), described in [The capabilities](#the-capabilities).

`conftest.py` uses `pytest_generate_tests` to run **every test once per device key**:

```
test_successful_checkout[pixel]
test_successful_checkout[samsung]
test_successful_checkout[android-14]
```

`pytest -n 6` (pytest-xdist) then spreads these across 6 parallel workers, each with its
own Sauce session.

### 2. The `driver` fixture

```python
@pytest.fixture
def driver(request, device):                      # device = "pixel", "samsung", ...
    caps = copy.deepcopy(CAPABILITIES[device])    # the hardcoded capabilities
    caps["sauce:options"].update({"username": ..., "accessKey": ..., "build": ...,
                                  "name": request.node.originalname})
    drv = webdriver.Remote(settings.HUB_URL, options=UiAutomator2Options().load_capabilities(caps))
    yield drv                                     # ← the test runs here
    drv.execute_script("sauce:job-result=passed") # or failed
    drv.quit()                                    # always runs
```

From the command line to the device:

```
pytest --devices pixel
  → conftest.py  pytest_addoption        registers --devices
  → conftest.py  _selected_devices       checks "pixel" is a key in CAPABILITIES
  → conftest.py  pytest_generate_tests   runs each test with device="pixel"
  → conftest.py  driver fixture          CAPABILITIES["pixel"] + runtime values
  → webdriver.Remote                     Sauce Labs allocates a matching phone
```

Fixtures build on each other, so a test asks only for the state it needs:

| Fixture | Gives the test |
|---|---|
| `driver` | A fresh Appium session on a real device |
| `login_page` | The app open on the login screen |
| `shop_page` | Already logged in as `doglover`, on the shop screen |

### 3. Inside `conftest.py`: hooks, fixtures and helpers

pytest loads `conftest.py` automatically, before any test. Loading it only **defines** the
functions. None of them runs at import, and their order in the file doesn't matter.
pytest calls each one at the right moment by its **name**.

The functions come in three kinds:

#### Hooks: reserved names that pytest calls itself

A function whose name is a known pytest hook is called by pytest at a fixed point in the run.
**The function name and its parameter names are fixed.** If you rename one, pytest silently
stops calling it. For example, renaming `pytest_addoption` gives
`error: unrecognized arguments: --devices`.

| Hook | When pytest calls it | Purpose here |
|---|---|---|
| `pytest_addoption(parser)` | At startup, before reading the command line | Registers the `--devices` option (default: the `DEVICES` env var, or all devices) |
| `pytest_configure(config)` | Once per process, after options are parsed | Fixes the Sauce **build name** once in the main process, so all parallel workers report into the same build |
| `pytest_generate_tests(metafunc)` | While collecting, once per test function | Runs every test once per selected device: `test_x[pixel]`, `test_x[samsung]`, ... |
| `pytest_runtest_makereport(item, call)` | After each test phase: setup, call, teardown | Stores the phase result on the test (`rep_call`) so `driver` knows whether the test passed |

The full list of hooks is in the pytest docs:
[API Reference → Hooks](https://docs.pytest.org/en/stable/reference/reference.html#hooks).

#### Fixtures: `@pytest.fixture`, called before each test that asks for them

A test asks for a fixture by naming it as a parameter: `def test_x(shop_page):`. pytest
calls the fixture before the test and passes in its result. Fixture names are free to
choose, but tests depend on them, so renaming one means updating the tests that use it.

| Fixture | Depends on | When it runs | Purpose |
|---|---|---|---|
| `driver(request, device)` | `device` | Before **every** test that needs it, plus cleanup after | Opens a Sauce session: `CAPABILITIES[device]` + credentials, build and test name. After the test: saves failure artifacts if needed, sets the Sauce job result, calls `quit()` |
| `login_page(driver)` | `driver` | Before the test | Waits for the login screen and returns a `LoginPage` |
| `shop_page(login_page)` | `login_page` | Before the test | Logs in as `doglover` and returns a `ShopPage` |

`device` isn't a function. Its value (`"pixel"`, `"samsung"`, ...) comes from
`pytest_generate_tests`.

**`yield drv`** divides `driver` into before and after the test:

```python
drv = webdriver.Remote(...)   # SETUP: runs before the test
yield drv                     # hands drv to the test and pauses; the test runs now
drv.quit()                    # TEARDOWN: runs after the test, even if it failed
```

The cleanup after `yield` always runs, so a failed test still releases its real device.

#### Helpers: plain functions, called only by our own code

pytest doesn't know about these. They run only when another function calls them. The
leading `_` means "internal helper". You can rename them freely, along with their callers.

| Helper | Called from | When | Purpose |
|---|---|---|---|
| `_selected_devices(config)` | `pytest_generate_tests` | While collecting | Turns `--devices pixel,samsung` into a list of keys and rejects unknown ids |
| `_save_failure_artifacts(drv, node)` | `driver`, after `yield` | After a test, **only if it failed** | Saves a screenshot and the UI tree to `reports/failures/` |

#### Order of a run

```
pytest tests/test_login.py --devices pixel

 1. pytest.ini                  settings are read
 2. conftest.py                 imported: functions defined, config/ and pages/ imported
 3. pytest_addoption            --devices registered
 4. pytest_configure            build name fixed
 5. tests/test_login.py         imported, test functions found
 6. pytest_generate_tests       each test × each device  (calls _selected_devices)
 7. for every test:
      setup     driver (until yield) → login_page → shop_page    ┐ pytest_runtest_makereport
      call      the test function                                 │ after each phase
      teardown  driver after yield (calls _save_failure_artifacts │
                if the test failed) → job result → quit()         ┘
 8. reports/junit.xml written, summary printed
```

#### In parallel (`-n 2`)

pytest-xdist starts separate **worker processes**, and each one imports its own copy of
`conftest.py`. Each worker runs one test at a time and calls `driver()` for every test, so
every test gets a fresh Sauce session. At most `-n` sessions run at once.

```
main process   imports conftest.py, collects tests, hands them to free workers
worker gw0     imports conftest.py → test → driver() → session → quit() → next test ...
worker gw1     imports conftest.py → test → driver() → session → quit() → next test ...
```

### 4. Page Objects

Each screen is a class. Locators and how to use them stay in the page, and tests
describe behaviour:

```python
def test_successful_checkout(shop_page):
    cart = shop_page.add_to_cart(ORANGE_SWEATER.id).add_to_cart(XMAS_SWEATER.id).open_cart()
    checkout = cart.checkout()
    confirmation = checkout.fill_shipping("Rex the Dog", "1 Bark Street").place_order()

    assert confirmation.title() == "Payment successful!"
    assert confirmation.amount() == ORANGE_SWEATER.price + XMAS_SWEATER.price
```

Actions that move to another screen return that screen's page object
(`open_cart()` → `CartPage`, `place_order()` → `OrderCompletePage`), so a test reads as
the user's path through the app.

### 5. Locators

The app's Compose `testTag`s are exposed as Android resource-ids (`testTagsAsResourceId`).
`by_tag("login_button")` in `base_page.py` turns a tag into a locator.

---

## Adding things

**A new test**: create `tests/test_something.py` and ask for a fixture:

```python
def test_logout_returns_to_login(shop_page):
    login = shop_page.logout()
    assert login.is_displayed(login.LOGIN_BUTTON)
```

It automatically runs on every device.

**A new device**: copy an entry in `config/capabilities.py`, give it a new key, and change
`appium:deviceName` / `appium:platformVersion`. See
[Choosing devices with regular expressions](#choosing-devices-with-regular-expressions).

**A new screen**: add a class in `pages/` that extends `BasePage`, with its locators
as class attributes and its actions as methods.

---

## Azure DevOps

The repository doesn't include a pipeline file. Create the pipeline in Azure DevOps
(**Pipelines → New pipeline**, pick this GitHub repo). The framework is already set up
for CI. The pipeline needs these steps:

| Step | How |
|---|---|
| Credentials | A variable group (**Pipelines → Library**) with `SAUCE_USERNAME` and `SAUCE_ACCESS_KEY`, the key marked secret. Secret variables must be mapped explicitly into the test step's `env:` |
| Python | `UsePythonVersion` task, Python 3.10 or newer |
| Install | `pip install -r requirements.txt` (no virtual environment needed on a hosted agent) |
| Run | `pytest -n 6 --reruns 1`. Keep `-n` within your Sauce Labs real-device concurrency |
| Test results | `PublishTestResults` task, format **JUnit**, file `reports/junit.xml`, condition `succeededOrFailed()` so results publish even when tests fail |
| Failure screenshots (optional) | `PublishPipelineArtifact` task for `reports/failures`, condition `failed()` |

What you get without extra configuration:

- **Sauce build name**: taken from Azure's predefined variables `BUILD_DEFINITIONNAME`
  and `BUILD_BUILDNUMBER`, so each pipeline run maps to one Sauce Labs build.
- **Tests tab**: one row per test and device, e.g. `test_valid_user_can_log_in[pixel]`.
- **Sauce job links**: in each test's output in the JUnit report.

---

## Troubleshooting & lessons learned (Compose + Appium)

| Symptom | Cause / fix |
|---|---|
| App not found / install fails | The APK isn't in the selected data center's storage |
| Session waits, then "no device available" | No free phone matches `appium:deviceName` + `appium:platformVersion`. Broaden the regex or change the version |
| Text typed into a field is appended to the old text | On Compose fields `clear()` does nothing and `send_keys` appends. `BasePage.type()` uses `mobile: replaceElementValue` |
| `AppiumBy.ID` doesn't find elements | It prepends the package (`com.pawknits.demo:id/...`). Compose tags have no package, so use `by_tag()` (UiSelector `resourceId`) |
| `UiScrollable.scrollIntoView` doesn't find list items | It's unreliable with Compose lazy lists. `BasePage.scroll_to()` swipes with `mobile: scrollGesture` and checks after each swipe |
| A product works on one phone and fails on another | Screen and font size change the layout (some phones show 1 column instead of 2). Always `scroll_to()` before tapping |
| Tests wait in queue | `-n` is higher than your real-device concurrency |

To inspect the live UI tree, use [Appium Inspector](https://github.com/appium/appium-inspector)
with the same capabilities, or open `reports/failures/*.xml` after a failed run.
