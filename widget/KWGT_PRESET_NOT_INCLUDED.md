# Why Isn't a Pre-compiled `.kwgt` File Included?

The final `.kwgt` preset archive should be exported directly from the KWGT app on the user's Android device.

Reasons:
1. The `.kwgt` zip bundle includes internal metadata and schema definitions specific to the installed Kustom app version;
2. System fonts, iconography, screen densities, and bitmap assets vary per Android device;
3. Generating a synthetic `.kwgt` archive outside of Kustom frequently causes schema corruption or import errors on Android;
4. Credentials and tokens must be configured locally on the device and must never be bundled into public repositories.

This repository provides:
- Complete component hierarchy trees;
- Component contracts;
- Global variable definitions;
- Kustom Flows blueprints;
- API endpoint specifications;
- Data contracts and normalizations;
- ASCII UI mockups;
- Catppuccin Mocha color tokens;
- Verification and test suites.

After assembling the components in KWGT according to this blueprint, use the **Export Preset** action within KWGT and save your `.kwgt` file alongside this blueprint.
