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
        '#DAA520': '&',  // Yellow
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
        const pixelX = x * snapSize; // Use snapSize instead of hardcoded 10
        const pixelY = y * snapSize;

        const onLeftOrRight = (pixelX === rect.x || pixelX === rect.x + rect.width - snapSize) &&
            (pixelY >= rect.y && pixelY < rect.y + rect.height);
        const onTopOrBottom = (pixelY === rect.y || pixelY === rect.y + rect.height - snapSize) &&
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
        '#DAA520': 'Yellow', '#ff00ff': 'Purple'
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


    return finalPrompt;
}



// Updated snap function
function snapToGrid(coord) {
    return Math.floor(coord / snapSize) * snapSize;
}

// Get touch position (similar to getMousePos but for touch)
function getTouchPos(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const touch = e.touches[0]; // First finger
    const x = (touch.clientX - rect.left) * scaleX;
    const y = (touch.clientY - rect.top) * scaleY;

    return {
        x: snapToGrid(x),
        y: snapToGrid(y)
    };
}
