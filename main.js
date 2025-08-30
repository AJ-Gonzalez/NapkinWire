const canvas = document.getElementById('drawingCanvas');

document.getElementById('layoutPicker').addEventListener('change', function (e) {
    const layout = e.target.value;

    switch (layout) {
        case 'desktop':
            canvas.width = 800;
            canvas.height = 450;
            break;
        case 'mobile':
            canvas.width = 450;
            canvas.height = 800;
            break;
        case 'square':
            canvas.width = 600;
            canvas.height = 600;
            break;
    }

    // Clear the canvas after resize
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Reset your rectangles array if you have one
    rectangles = [];
});

let currentColor = '#ff0000'; // Start with red

// Set initial active state
document.querySelector('.color-btn[data-color="#ff0000"]').classList.add('active');

// Handle color button clicks
document.querySelectorAll('.color-btn').forEach(button => {
    button.addEventListener('click', function () {
        // Clear all active states
        document.querySelectorAll('.color-btn').forEach(btn => btn.classList.remove('active'));

        // Set this button as active
        this.classList.add('active');

        // Update current color
        currentColor = this.dataset.color;
        // In your color button click handler
        document.getElementById('activeColorName').textContent = this.textContent;

        // In your color button click handler, add:
        const indicator = document.getElementById('activeColorName');
        const colorDisplay = document.querySelector('.active-color-display');

        indicator.textContent = this.textContent;
        colorDisplay.style.backgroundColor = currentColor;

        // Adjust text color for readability
        if (currentColor === '#ffff00') {
            colorDisplay.style.color = 'black'; // Yellow needs dark text
        } else {
            colorDisplay.style.color = 'white';
        }

        console.log('Selected color:', currentColor); // For debugging
    });
});

const ctx = canvas.getContext('2d');
let rectangles = [];
let isDrawing = false;
let startX, startY;
let currentRect = null;

// Snap coordinates to 10px grid
function snapToGrid(coord) {
    return Math.floor(coord / 10) * 10;
}

// Get mouse position relative to canvas
function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    return {
        x: snapToGrid(x),
        y: snapToGrid(y)
    };
}

// Mouse down - start drawing
canvas.addEventListener('mousedown', function (e) {
    const pos = getMousePos(e);
    isDrawing = true;
    startX = pos.x;
    startY = pos.y;
});

// Replace your existing mouse up event listener with this:
document.addEventListener('mouseup', function (e) {
    if (!isDrawing) return;

    const pos = getMousePos(e);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Only add if rectangle has actual size
    if (Math.abs(width) >= 10 && Math.abs(height) >= 10) {
        rectangles.push({
            x: Math.min(startX, pos.x),
            y: Math.min(startY, pos.y),
            width: Math.abs(width),
            height: Math.abs(height),
            color: currentColor
        });

        // Auto-generate ASCII and input fields immediately
        updateLayout();
    }

    isDrawing = false;
    redrawCanvas();
});

document.addEventListener('mousemove', function (e) {
    if (!isDrawing) return;

    const pos = getMousePos(e);
    const width = pos.x - startX;
    const height = pos.y - startY;

    // Redraw everything + show preview rectangle
    redrawCanvas();

    // Draw the preview rectangle
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = 2;
    if (currentColor === '#ff00ff') {
        // Purple rectangles get filled
        ctx.fillStyle = currentColor;
        ctx.fillRect(startX, startY, width, height);
    } else {
        // Other colors just get stroked
        ctx.strokeRect(startX, startY, width, height);
    }
});


// Also update the undo function to auto-regenerate:
function undoLastRectangle() {
    if (rectangles.length > 0) {
        rectangles.pop();
        redrawCanvas();
        updateLayout(); // Auto-regenerate after undo
    }
}

// New function that handles both ASCII and input field generation:
function updateLayout() {
    const ascii_out = generateASCII();
    document.getElementById('ascii-preview').textContent = ascii_out;
    generateInputFields();
}

document.getElementById('undoBtn').addEventListener('click', undoLastRectangle);

let isTUIMode = false;

document.getElementById('tuiMode').addEventListener('change', function (e) {
    isTUIMode = e.target.checked;
});

function redrawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    rectangles.forEach(rect => {
        if (rect.color === '#ff00ff') { // Purple text rectangles
            ctx.fillStyle = rect.color;
            ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
        } else {
            ctx.strokeStyle = rect.color;
            ctx.lineWidth = 2;
            ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
        }
    });
}

function generateASCII() {
    const colorToChar = {
        '#ff0000': '#',  // Red
        '#00ff00': '@',  // Green
        '#0000ff': '%',  // Blue
        '#ffff00': '&',  // Yellow
        '#ff00ff': '.'   // Purple - will be replaced with numbers
    };

    const gridWidth = Math.floor(canvas.width / 10);
    const gridHeight = Math.floor(canvas.height / 10);
    let asciiOutput = '';

    // Track text areas for numbering
    let textAreaCounter = 1;
    const textAreaNumbers = new Map(); // rect index -> number

    // Assign numbers to text areas first
    rectangles.forEach((rect, index) => {
        if (rect.color === '#ff00ff') {
            textAreaNumbers.set(index, textAreaCounter++);
        }
    });

    for (let y = 0; y < gridHeight; y++) {
        let row = '';
        for (let x = 0; x < gridWidth; x++) {
            let char = ' '; // default empty space

            for (let rectIndex = 0; rectIndex < rectangles.length; rectIndex++) {
                const rect = rectangles[rectIndex];

                if (isOnPerimeter(x, y, rect)) {
                    if (rect.color === '#ff00ff') {
                        // Use the assigned number for this text area
                        char = textAreaNumbers.get(rectIndex).toString();
                    } else {
                        char = colorToChar[rect.color] || '?';
                    }
                    break;
                }
            }
            row += char;
        }
        asciiOutput += row + '\n';
    }

    return asciiOutput;

    function isOnPerimeter(x, y, rect) {
        const pixelX = x * 10;
        const pixelY = y * 10;

        const onLeftOrRight = (pixelX === rect.x || pixelX === rect.x + rect.width - 10) &&
            (pixelY >= rect.y && pixelY < rect.y + rect.height);
        const onTopOrBottom = (pixelY === rect.y || pixelY === rect.y + rect.height - 10) &&
            (pixelX >= rect.x && pixelX < rect.x + rect.width);

        return onLeftOrRight || onTopOrBottom;
    }
}

function generateInputFields() {
    const container = document.getElementById('rectangle-dropdowns');
    container.innerHTML = ''; // Clear existing fields

    // Only generate fields for text areas (purple rectangles)
    let textAreaCounter = 1;

    rectangles.forEach((rect, index) => {
        if (rect.color === '#ff00ff') {
            const fieldDiv = document.createElement('div');
            fieldDiv.innerHTML = `
                <label>Text Area ${textAreaCounter}:</label>
                <input type="text" id="text_${index}" placeholder="e.g., Article title, User message, Navigation links">
            `;
            container.appendChild(fieldDiv);
            textAreaCounter++;
        }
    });
}
function getColorName(color) {
    const names = {
        '#ff0000': 'Red', '#00ff00': 'Green', '#0000ff': 'Blue',
        '#ffff00': 'Yellow', '#ff00ff': 'Purple'
    };
    return names[color] || 'Unknown';
}




function generateFinalPrompt() {
    const asciiLayout = generateASCII();
    const overallPurpose = document.getElementById('overall-purpose').value || 'web interface';
    const platform = document.getElementById('platform').value || 'vanilla JS';
    const isTUI = document.getElementById("tuiMode").checked;

    // Build create statement
    let createStatement = '';
    if (isTUI) {
        createStatement = `Create this TUI (Terminal User Interface) using ${platform}`;
    } else {
        createStatement = `Create this GUI using ${platform}`;
    }

    // Collect only text area descriptions
    let textAreaDescriptions = '';
    let textAreaCounter = 1;

    rectangles.forEach((rect, index) => {
        if (rect.color === '#ff00ff') {
            const textInput = document.getElementById(`text_${index}`);
            const description = textInput ? textInput.value : 'text content';
            textAreaDescriptions += `\nText Area ${textAreaCounter}: ${description}`;
            textAreaCounter++;
        }
    });

    // Build final prompt
    let finalPrompt = `${createStatement}, it will be used for a ${overallPurpose}

Using the following layout:

${asciiLayout}

Content areas:${textAreaDescriptions}

Please create a functional interface that matches this layout exactly. Use the visual structure shown in the ASCII art as your guide for positioning and proportions.`;

    // Display the prompt in the preview textarea
    document.getElementById('prompt-preview').value = finalPrompt;

    return finalPrompt;
}






document.getElementById("get_prompt").addEventListener('click', function () {
    // Generate the prompt
    const finalPrompt = generateFinalPrompt();

    // Copy to clipboard immediately
    navigator.clipboard.writeText(finalPrompt).then(() => {
        // Flash the button text
        const originalText = this.textContent;
        this.textContent = 'Copied to Clipboard!';
        this.style.backgroundColor = '#059669'; // Slightly different green

        setTimeout(() => {
            this.textContent = originalText;
            this.style.backgroundColor = 'var(--button_bg)'; // Back to original
        }, 1500);
    }).catch(() => {
        // Fallback if clipboard fails
        this.textContent = 'Copy failed - check preview';
        setTimeout(() => {
            this.textContent = 'Get Prompt!';
        }, 2000);
    });
});


// Reset canvas functionality - add this to main.js
document.getElementById("clear_canvas").addEventListener('click', function () {
    rectangles = [];
    redrawCanvas();
    document.getElementById('ascii-preview').textContent = '';
    document.getElementById('prompt-preview').value = '';
    document.getElementById('rectangle-dropdowns').innerHTML = '';

    // Clear the main input fields too
    document.getElementById('overall-purpose').value = '';
    document.getElementById('platform').value = '';
    // Remove this line - field doesn't exist anymore:
    // document.getElementById('text-areas').value = '';
    document.getElementById('tuiMode').checked = false;

    // Flash feedback
    const originalText = this.textContent;
    this.textContent = 'Cleared!';
    setTimeout(() => {
        this.textContent = originalText;
    }, 800);
});