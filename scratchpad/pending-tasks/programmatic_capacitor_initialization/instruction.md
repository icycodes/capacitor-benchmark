Integrating Capacitor into an automated CI/CD pipeline requires avoiding interactive CLI prompts that can halt or break the build process.

You need to write a bash script `init-capacitor.sh` that installs the core Capacitor dependencies and non-interactively initializes a Capacitor project named "MyApp" with the App ID "com.example.myapp" targeting the `dist` web directory. Following initialization, the script must install and add the iOS and Android platforms.

**Constraints:**
- Must exclusively use non-interactive CLI arguments and flags for the `npx cap init` command.
- Do NOT include any commands that trigger interactive prompts or require manual user input.