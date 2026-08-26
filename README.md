# LanyardBot

LanyardBot verifies that Discord members are students at a given institution by emailing a one-time code to their school address, then granting them a verified role.

![GitHub License](https://img.shields.io/github/license/bk0704/lanyardbot)

---
# Usage
1. Server admin or member with "Manage Guild" permissions enters `/verify role:` to put the verification message in a certain channel
2. User clicks on the "Verify" Button, and a modal appears asking the user to input their school email
3. If the bot validates the domain match(`@sheridancollege.ca`), generates a 6-digit OTP, saves it locally with a 15-minute expiry, and sends an ephemeral message with an "Enter OTP" button
4. User clicks "Enter OTP" which opens a second modal with a text input "Enter the 6-digit code"
5. Bot verifies the OTP against the database/local record:
	1. **Match & within 15 min:** Bot assigns the verified role, sends an ephemeral confirmation message, and clears the pending OTP.
	2. **Invalid or Expired:** Bot shows an error message prompting the user to try again.
---
This program is licensed under an MIT License, check [LICENSE](LICENSE) for more details