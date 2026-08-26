# LanyardBot

LanyardBot verifies that Discord members are students at a given institution by emailing a one-time code to their school address, then granting them a verified role.

![GitHub License](https://img.shields.io/github/license/bk0704/lanyardbot)

---
# Features
- Verify whether a discord user is a student at a college organization using a OTP sent to the email made specifically for the insitution
- The LanyardBot Network is a network within an educational institute when a person is verified on one organization, they're verified on all clubs for the institute
- Manual override for moderators
- Simple to use UI via modals for all servers
- Very easy setup
- Easy `/forgetme` command to have your email removed from the data base
- Currently only supports Sheridan College

# Background
The reason why I decided to build this discord bot is that I noticed there's a huge problem wih people joining college club servers only for them to be scam bots

---

# Usage
## Adding LanyardBot to a Server and setting it up
1. A server admin decided to add LanyardBot to their server 
2. The server admin then needs to input enter `/setup` in order to set up the bot, using that command will present a setup modal with these following options
	1. A RoleSelect with the label "What role do you want to choose as your verified role?"
	2. A ChannelSelect with the label "What channel do you want for the verification button to be"
	3. A Select with the label "What institution(secondary and post-secondary) is this organization/club for"(currently the only option is "Sheridan College, Canada" more will be added in the future)
	4. A button will say "Proceed 😎"
3. Once the proceed button is pressed, everything is set up and ready to go
4. If opted-in(default) all previously joined members will automatically receive the verified role
## Verifying members
- When a new user finishes with the community flow, the bot will start checking whether or not a member was already verified in another organization in the same institution
	- If the new member was indeed verified in another organization, then they will be automatically qualified(with an exception i'll go over in a sec)
- The other way someone can verify is someone who has managing roles permissions can override a verification by using `/override username:`
- In the verification channel
	- A verification button appears. When clicked it'll open a ticket channel, in this ticket channel there will be a modal with 3 things
		- A label that says "Enter your [institute] email"
		- A textbox to enter the email
		- An "Enter" button
	- When the user presses the enter button, the modal will close, and a message will be sent. The user will have 15 minutes to click the button on the follow up message which has then modal with the following
		- A label that says "Enter the OTP sent to your email"
		- A textbok to enter the OTP
		- A "Verify 👏" button
	- The user after that becomes officially verified

---
# Roadmap
- [ ] Include support for at least 5 more Canadian post-secondary institutions
- [ ] Switch from a OTP based verification to OIDC(for Sheridan College)

---
This program is licensed under an MIT License, check [LICENSE](LICENSE) for more details