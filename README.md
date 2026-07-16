# NapkinWire

![Napkinwire icon](web/icon-192.png)

From sketch to prompt in seconds.

**[Try it here!](https://www.napkinwire.lat/)**

## What it does

Sketch UI layouts with simple rectangles and instantly get LLM-ready prompts, or layout diagrams for Spect Driven Development. 

No accounts, no subscriptions, no BS. 

Free forever. 

**The problem:** Describing UI layouts to LLMs (or humans) in text is terrible. "Put a button on the right side, below the form, but not too close to the footer..." Yuck!

**The solution:** Draw rectangles. Get perfect prompts. Build your UI.

## Why this exists

Built because I needed to mock up UIs quickly for AI coding workflows. Started sketching on actual napkins, realized this could be better.

I wanted the feeling of sketching ideas on the back of a napkin or whiteboard - dead simple, no friction between idea and communication.

## How it works

1. **Draw rectangles** on a canvas (mobile-friendly)
2. **Purple rectangles** become text content areas  
3. **Label** what goes in each area ("User avatar", "Article title", etc.)
4. **Copy prompt** that actually works with ChatGPT, Claude, Cursor, etc.
5. **Generate code** in your LLM of choice


### UI Mockup Example

<details>

<summary>Here is a login form example, showcasing how the text labels work</summary>


```
Create this GUI using Vanilla JS with Tailwind CSS, it will be used for a Login form for my landing page



                                                     
           ###########################               
           # @@@@@@@@@@@@@@@@@@@@@@  #               
           # @  11111111111       @  #               
           # @@@@@@@@@@@@@@@@@@@@@@  #               
           #                         #               
           # @@@@@@@@@@@@@@@@@@@@@@  #               
           # @  22222222222       @  #               
           # @@@@@@@@@@@@@@@@@@@@@@  #               
           #                         #               
           #                         #               
           # &&&&&&&&&&&&&&&&&&&&    #               
           # &  333333333333    &    #               
           # &                  &    #               
           # &&&&&&&&&&&&&&&&&&&&    #               
           #                         #               
           #                         #               
           #                         #               
           # %%%%%%%    %%%%%%%%%    #               
           # %     %    %       %    #               
           # %444  %    % 5555  %    #               
           # %4 4  %    % 5555  %    #               
           # %444  %    %       %    #               
           # %     %    %       %    #               
           # %     %    %%%%%%%%%    #               
           # %%%%%%%                 #               
           #                         #               
           ###########################               
                                                     
                                                     



Content areas:
Text Area 1: Username or email field
Text Area 2: password field
Text Area 3: captcha (will add later) use placeholder text
Text Area 4: Log in button
Text Area 5: Sign in button


Please create a functional interface that matches this layout exactly. Use the visual structure shown in the ASCII art as your guide for positioning and proportions.

Additional requirements: 

Dark theme with blue accents. 
No rounded corners. 
```


</details>

## Features

- Works on mobile (PWA installable)
- Multiple layouts (desktop, mobile, square)
- Supports both GUI and TUI frameworks
- One-click copy to clipboard
- Completely free and open source
- No data leaves your device
- Also provides just the annotated diagram for Spec Driven Development


## Usage

Just start drawing. Everything updates automatically as you sketch.


*Want something specific? [Open an issue](https://github.com/AJ-Gonzalez/NapkinWire/issues)*

## Installation & Development

```bash
# Clone and run locally
git clone https://github.com/AJ-Gonzalez/NapkinWire.git
cd NapkinWire/web
python -m http.server 8000  # or your preferred local server

# No build step needed - vanilla JS keeps it simple
```

## Who this is for

- **Developers** who need quick UI mockups for AI coding workflows
- **Designers** who want to communicate ideas without Figma overhead
- **Anyone** who thinks better with visual layouts than pure text

## License

Licensed under Apache 2.0 - commercially friendly, use however you want.

## Contributing

PRs welcome. 

Keep it simple, keep it fast, keep it free.

---

*Built for the "sketch on a napkin" feeling we all miss.*
