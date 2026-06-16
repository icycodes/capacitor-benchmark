#!/usr/bin/env bash
# End-to-end check: type-check the project, compile session.ts to ESM, run the
# behavioral verifier against a real local HTTP fixture server.
PROJECT_DIR="${PROJECT_DIR:-/home/user/myproject}"
VERIFIER_DIR="${VERIFIER_DIR:-/home/user/verifier}"
BUILD_DIR="${BUILD_DIR:-/tmp/verify-build}"

cd "$PROJECT_DIR" || { echo "FAILURE: cannot cd to $PROJECT_DIR"; echo "RESULT: FAIL"; exit 1; }

echo "[run_session_check] step 1/3: npx tsc --noEmit"
npx --no-install tsc --noEmit
TSC_NOEMIT_EXIT=$?
if [ $TSC_NOEMIT_EXIT -ne 0 ]; then
  echo "FAILURE: tsc --noEmit returned $TSC_NOEMIT_EXIT"
  echo "RESULT: FAIL"
  exit 1
fi

echo "[run_session_check] step 2/3: compile src/auth/session.ts"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
printf '{"type":"module"}\n' > "$BUILD_DIR/package.json"
npx --no-install tsc \
  --outDir "$BUILD_DIR" \
  --module esnext \
  --target es2022 \
  --moduleResolution node \
  --rootDir "$PROJECT_DIR/src" \
  --esModuleInterop \
  --strict \
  --skipLibCheck \
  --noEmit false \
  "$PROJECT_DIR/src/auth/session.ts"
TSC_BUILD_EXIT=$?
if [ $TSC_BUILD_EXIT -ne 0 ]; then
  echo "FAILURE: tsc compile of session.ts returned $TSC_BUILD_EXIT"
  echo "RESULT: FAIL"
  exit 1
fi
if [ ! -f "$BUILD_DIR/auth/session.js" ]; then
  echo "FAILURE: expected compiled output at $BUILD_DIR/auth/session.js"
  echo "RESULT: FAIL"
  exit 1
fi

echo "[run_session_check] step 3/3: behavioral verifier"
COMPILED_SESSION_PATH="$BUILD_DIR/auth/session.js" \
  node "$VERIFIER_DIR/verify_session.mjs"
exit $?
