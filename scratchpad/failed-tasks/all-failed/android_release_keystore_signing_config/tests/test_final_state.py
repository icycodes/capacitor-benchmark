import os
import re
import shutil
import subprocess

import pytest

PROJECT_DIR = "/home/user/myproject"
ANDROID_DIR = os.path.join(PROJECT_DIR, "android")
APP_DIR = os.path.join(ANDROID_DIR, "app")
BUILD_GRADLE = os.path.join(APP_DIR, "build.gradle")
KEYSTORE_PROPERTIES = os.path.join(ANDROID_DIR, "keystore.properties")
KEYSTORE_PROPERTIES_EXAMPLE = os.path.join(ANDROID_DIR, "keystore.properties.example")

REQUIRED_KEYS = (
    "RELEASE_STORE_FILE",
    "RELEASE_STORE_PASSWORD",
    "RELEASE_KEY_ALIAS",
    "RELEASE_KEY_PASSWORD",
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _strip_line_comments(source: str) -> str:
    """Remove `//` and `/* ... */` style comments to make pattern matches robust."""
    no_block = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


def _extract_balanced_block(source: str, header_regex: str) -> str | None:
    """Return the body of the first `{ ... }` block whose header matches the regex.

    The regex is matched against the source up to (but not including) the
    opening brace. Returns None if no match is found.
    """
    match = re.search(header_regex, source)
    if not match:
        return None
    idx = source.find("{", match.end() - 1)
    if idx == -1:
        return None
    depth = 0
    for i in range(idx, len(source)):
        ch = source[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[idx + 1 : i]
    return None


@pytest.fixture(scope="module")
def gradle_source() -> str:
    assert os.path.isfile(BUILD_GRADLE), (
        f"Expected {BUILD_GRADLE} to exist after the task is complete."
    )
    return _strip_line_comments(_read(BUILD_GRADLE))


def test_properties_loaded_at_top_of_build_gradle(gradle_source: str):
    # Locate the start of the `android {` block (top-level) and assert that a
    # Properties load happens earlier in the file.
    android_match = re.search(r"\bandroid\s*\{", gradle_source)
    assert android_match, (
        "Could not locate the top-level `android { ... }` block in build.gradle."
    )
    prelude = gradle_source[: android_match.start()]
    assert "Properties" in prelude, (
        "Expected a `Properties` instance to be loaded before the `android` "
        "block in android/app/build.gradle (e.g. `def keystoreProperties = new Properties()`)."
    )
    assert re.search(
        r"keystore\.properties", prelude
    ), (
        "Expected the prelude of android/app/build.gradle to reference "
        "`keystore.properties` so secrets are loaded from that file."
    )
    assert re.search(
        r"\.load\s*\(", prelude
    ), (
        "Expected `Properties.load(...)` (or equivalent) to be invoked before the "
        "`android { ... }` block."
    )


def test_signing_configs_release_block_exists(gradle_source: str):
    android_body = _extract_balanced_block(gradle_source, r"\bandroid\s*\{")
    assert android_body is not None, (
        "Failed to extract the body of the top-level `android { ... }` block."
    )
    signing_body = _extract_balanced_block(android_body, r"\bsigningConfigs\s*\{")
    assert signing_body is not None, (
        "Expected a `signingConfigs { ... }` block inside the `android { ... }` "
        "block of android/app/build.gradle."
    )
    release_body = _extract_balanced_block(signing_body, r"\brelease\s*\{")
    assert release_body is not None, (
        "Expected a `release { ... }` sub-block inside `signingConfigs { ... }`."
    )
    for key in REQUIRED_KEYS:
        assert key in release_body, (
            f"Expected the `signingConfigs.release` block to reference the "
            f"`{key}` property from the loaded keystore.properties."
        )
    # Store file must be wrapped in file(...).
    assert re.search(
        r"file\s*\(.*RELEASE_STORE_FILE.*\)", release_body, flags=re.DOTALL
    ), (
        "The `RELEASE_STORE_FILE` lookup in `signingConfigs.release` must be "
        "wrapped in a `file(...)` call so Gradle resolves it as a File."
    )


def test_release_build_type_uses_signing_config(gradle_source: str):
    android_body = _extract_balanced_block(gradle_source, r"\bandroid\s*\{")
    assert android_body is not None, "Missing top-level `android { ... }` block."
    build_types_body = _extract_balanced_block(android_body, r"\bbuildTypes\s*\{")
    assert build_types_body is not None, (
        "Expected a `buildTypes { ... }` block inside the `android { ... }` block."
    )
    release_body = _extract_balanced_block(build_types_body, r"\brelease\s*\{")
    assert release_body is not None, (
        "Expected a `release { ... }` sub-block inside `buildTypes { ... }` "
        "so the new signing config can be attached to release builds."
    )
    assert re.search(
        r"signingConfig\s*=?\s*signingConfigs\.release", release_body
    ), (
        "Expected `buildTypes.release` to declare "
        "`signingConfig signingConfigs.release` "
        "(or `signingConfig = signingConfigs.release`)."
    )


def test_keystore_properties_example_exists_with_all_keys():
    assert os.path.isfile(KEYSTORE_PROPERTIES_EXAMPLE), (
        f"Expected example file {KEYSTORE_PROPERTIES_EXAMPLE} to exist so other "
        "contributors know which keys to populate."
    )
    content = _read(KEYSTORE_PROPERTIES_EXAMPLE)
    for key in REQUIRED_KEYS:
        assert re.search(
            rf"^\s*{re.escape(key)}\s*=", content, flags=re.MULTILINE
        ), (
            f"Expected key `{key}=...` in {KEYSTORE_PROPERTIES_EXAMPLE} "
            "(one declaration per line)."
        )


def test_real_keystore_properties_absent():
    assert not os.path.exists(KEYSTORE_PROPERTIES), (
        f"{KEYSTORE_PROPERTIES} must NOT exist; only the example file should "
        "be committed."
    )


def test_gitignore_ignores_keystore_properties():
    # Create an empty placeholder so git check-ignore can resolve the path.
    created = False
    try:
        if not os.path.exists(KEYSTORE_PROPERTIES):
            with open(KEYSTORE_PROPERTIES, "w") as f:
                f.write("")
            created = True
        result = subprocess.run(
            ["git", "check-ignore", "-q", "android/keystore.properties"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            "Expected `android/keystore.properties` to be matched by a "
            ".gitignore rule. `git check-ignore` returned "
            f"exit={result.returncode}, stdout={result.stdout!r}, "
            f"stderr={result.stderr!r}."
        )
    finally:
        if created and os.path.exists(KEYSTORE_PROPERTIES):
            os.remove(KEYSTORE_PROPERTIES)


def test_gitignore_does_not_ignore_example_file():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "android/keystore.properties.example"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        "Expected `android/keystore.properties.example` to NOT be ignored by "
        "git. `git check-ignore` returned "
        f"exit={result.returncode}, stdout={result.stdout!r}, "
        f"stderr={result.stderr!r}."
    )


def test_gradle_build_script_still_parses():
    # Copy the example to a real keystore.properties so the Properties.load call
    # succeeds at evaluation time. The placeholder values do not need to point
    # to a real keystore for `./gradlew help` to evaluate the build script.
    assert os.path.isfile(KEYSTORE_PROPERTIES_EXAMPLE), (
        f"Cannot run gradle parse check without {KEYSTORE_PROPERTIES_EXAMPLE}."
    )
    shutil.copyfile(KEYSTORE_PROPERTIES_EXAMPLE, KEYSTORE_PROPERTIES)
    try:
        result = subprocess.run(
            ["./gradlew", "help", "-q", "--offline"],
            cwd=ANDROID_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, (
            "Expected `./gradlew help -q --offline` to succeed after applying "
            "the signing config. Gradle reported a parse/evaluation error:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    finally:
        if os.path.exists(KEYSTORE_PROPERTIES):
            os.remove(KEYSTORE_PROPERTIES)
