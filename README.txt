TextCanvas is an app made by Zachory Pelletier. Created using Gemini 1.5 Pro AI model using Google AI Studio.

TextCanvas is a sophisticated, dark-themed Flask web application developed by Zachory Pelletier that features real-time single and batch Image-to-Text conversion with advanced subpixel rendering, matrix effects, and dithering customization options.

File Mapping for TextCanvas

TextCanvas/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   └── style.css
└── templates/
    ├── base.html       (Main Layout)
    ├── index.html      (Home / Dashboard)
    ├── page1.html      (Instructions)
    ├── page2.html      (About)
    ├── page3.html      (IMG to Text Generator)
    └── page4.html      (IMG to Text Batch Generator)

  

AI Prompt:

Project: Build a Flask (Python) web application called 'TextCanvas'.

Design Theme:
Use Bootstrap 5 'Simplex' theme but enforce a strict Red (#d9230f) and Black (#000000) Dark/Light mode color scheme via CSS overrides.

File Structure & Functionality:

    app.py: Main logic using Flask, Pillow (PIL), and Requests to process images into HTML text representations via API. Handles URL retrieval with browser headers to prevent blocking.

    templates/base.html: Base layout file containing the Red-themed Navbar, Footer, and Theme Toggle logic.

    templates/index.html: Dashboard page with a 4-card grid layout for navigation. Implements keyboard navigation (Arrow Keys + Enter).

    templates/page1.html: Instructions page explaining Source selection and Batch limits.

    templates/page2.html: About page crediting Zachory Pelletier and explaining the Subpixel logic.

    templates/page3.html: IMG to Text Generator.

        Features strict Drag & Drop or URL input (mutually exclusive).

        Real-time live preview with auto-scaling.

        Options for Subpixel, Matrix, ASCII, and Dithering.

        Unlimited PNG downloads.

    templates/page4.html: IMG to Text Batch Generator.

        Allows dragging up to 10 images or pasting 10 URLs.

        Generates a grid of live previews.

        Allows individual deletion (Red 'X') and individual downloading of processed images.

Specific Logic Implemented:

    Subpixel Rendering: Uses the Upper Half Block (▀) character to render two vertical pixels per character cell.

    Batch Constraints: Strict 10-image limit with auto-revert if exceeded.

    Drag & Drop: Custom CSS drag zones that replace standard file input buttons.

    Theme: Persistent Dark/Light mode saved to LocalStorage.