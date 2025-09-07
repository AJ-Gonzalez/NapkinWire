# NapkinWire

![Napkinwire icon](web/icon-192.png)

From sketch to prompt in seconds.

**[Try it here!](https://www.napkinwire.lat/)** | **[Demo Video](#demo)** | **[Examples](#examples)**

## What it does

Sketch UI layouts with simple rectangles and instantly get LLM-ready prompts.

Give your LLM a diagram of your process it can actually understand.

No accounts, no subscriptions, no BS.

**The problem:** Describing UI layouts or business processes to LLMs (or humans) in text is terrible. "Put a button on the right side, below the form, but not too close to the footer..." 🤮

**The solution:** Draw rectangles. Get perfect prompts. Build your UI, get your LLM to know your process.

## Why this exists

Built because I needed to mock up UIs quickly for AI coding workflows. Started sketching on actual napkins, realized this could be better.

I wanted the feeling of sketching ideas on the back of a napkin or whiteboard - dead simple, no friction between idea and communication.

**Real world usage:** I used NapkinWire to design NapkinWire's own homepage. It worked on the first try.

## Demo

### UI

[![UI Demo](https://img.youtube.com/vi/UkBR1bfjrr8/0.jpg)](https://www.youtube.com/watch?v=UkBR1bfjrr8)

### Diagrams


[![Diagram Demo](https://img.youtube.com/vi/tobQSC0ESPI/0.jpg)](https://www.youtube.com/watch?v=tobQSC0ESPI)


## How it works

1. **Draw rectangles** on a canvas (mobile-friendly)
2. **Purple rectangles** become text content areas  
3. **Label** what goes in each area ("User avatar", "Article title", etc.)
4. **Copy prompt** that actually works with ChatGPT, Claude, Cursor, etc.
5. **Generate code** in your LLM of choice

## Examples

These are the sample of each demo Gif.

### UI mockup

<details>

<summary>From the Login form demo, here is the prompt</summary>


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


### Diagram that the LLM can understand.

<details> 

<summary>Here is a diagram example from the gif, it shows onboarding a customer</summary>


```
Here is my Customer onboarding for my SaaS represented as a diagram:

                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                          44444444444444444444444444                      999999    
                                          4                        4                     999  999   
                                          4                        4            666     99      99  
                                          4                        4           66 66    99      99  
                                          4                        4          66   66   99      99  
                                          4                        4        66       66 99      99  
                                          4                        4        66       66 99      99  
                                          4                        4          66   66    999  999   
                                          4                        4           66 66      999999    
                                          4                        4            666                 
                                          44444444444444444444444444                                
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
        1                                                                                           
     1111111                                                           888888888888888888888        
    111111111       2222222222222                                      8                   8        
   111     111      2           2              33                      8                   8        
   11       11      2           2             3333                     8                   8        
   11       11      2           2           33    33                   8                   8        
  111       111     2           2          33      33                  8                   8        
   11       11      2           2        33          33                8                   8        
   11       11      2           2        33          33                8                   8        
   111     111      2           2          33      33                  8                   8        
    111111111       2222222222222           33    33                   8                   8        
     1111111                                  3333                     888888888888888888888        
        1                                      33                                                   
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                           55555555555555555555555555           7                   
                                           5                        5          777        1010101010     
                                           5                        5         77 77      10101010101010    
                                           5                        5        77   77    1010     1010   
                                           5                        5       77     77   1010     1010   
                                           5                        5       77     77   10       10   
                                           5                        5        77   77    10       10   
                                           5                        5         77 77     1010     1010   
                                           5                        5          777      1010     1010   
                                           55555555555555555555555555           7        10101010101010    
                                                                                          1010101010     
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    


Legend:
1: Customer joins (Start/End Point)
2: Send welcome email (Process/Action)
3: is b2b? (Decision Point)
4: B2B customer, connect with account rep (Process/Action)
5: B2C, connect with AI chatbot rep (Process/Action)
6: issue? (Decision Point)
7: issue? (Decision Point)
8: If there is an issue escalate to L2 rep (Process/Action)
9: Success! (Start/End Point)
10: Success! (Start/End Point)


Connections:
"Customer joins" → "Send welcome email"
"is b2b?" → "B2B customer, connect with account rep"
"is b2b?" → "B2C, connect with AI chatbot rep"
"Send welcome email" → "is b2b?"
"issue?" → "If there is an issue escalate to L2 rep"
"B2B customer, connect with account rep" → "issue?"
"Success!" → "Success!"
"B2C, connect with AI chatbot rep" → "issue?"
"issue?" → "If there is an issue escalate to L2 rep"
"issue?" → "Success!"

Additional context:
This starts with a customer that just joined
```

</details>


## Features

- ✅ Works on mobile (PWA installable)
- ✅ Touch drawing with snap-to-grid
- ✅ Multiple layouts (desktop, mobile, square)
- ✅ Supports both GUI and TUI frameworks
- ✅ One-click copy to clipboard
- ✅ Completely free and open source
- ✅ No data leaves your device

## Anti-features (by design)

- ❌ No user accounts or login
- ❌ No data collection or tracking
- ❌ No subscription fees  
- ❌ No complex design tools or learning curve
- ❌ No cloud dependencies

## Usage

Just start drawing. Everything updates automatically as you sketch.

**Pro tip:** Use purple rectangles for any area that needs custom content (text, images, forms, etc.).

## Roadmap

- [*] **MCP Server** - Claude Desktop integration for seamless sketch → code workflow (In development!)
- [ ] **Template library** - Common UI patterns for faster sketching
- [ ] **Advanced export options** - SVG, and more format support

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
- **Product managers** explaining processes and user flows to LLMs
- **Business analysts** documenting workflows and system diagrams  
- **Designers** who want to communicate ideas without Figma overhead  
- **Anyone** who thinks better with visual layouts than pure text

## License

Licensed under Apache 2.0 - commercially friendly, use however you want.

## Contributing

PRs welcome. Philosophy: keep it simple, keep it fast, keep it free.

---

*Built with ❤️ for the "sketch on a napkin" feeling we all miss.*
