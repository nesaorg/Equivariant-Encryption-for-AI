function initializeToken() {
  let token = localStorage.getItem('user_token'); // Check for an existing token in localStorage
  if (!token) {
    token = crypto.randomUUID(); // Generate a new UUID if none exists
    localStorage.setItem('user_token', token); // Store the token in localStorage
  }
  return token;
}

// Run token initialization on page load
const userToken = initializeToken();

// Pass the token to the backend (Gradio integration)
document.addEventListener("DOMContentLoaded", () => {
  const tokenInput = document.querySelector('input[name="state"]'); // Locate the hidden state input
  if (tokenInput) {
    tokenInput.value = userToken; // Set the token value for backend use
  }
  
});


let main_parent = document.getElementById("chat-tab").parentNode;
let extensions = document.getElementById("extensions");

main_parent.childNodes[0].classList.add("header_bar");
main_parent.style = "padding: 0; margin: 0";
main_parent.parentNode.style = "gap: 0";
main_parent.parentNode.parentNode.style = "padding: 0";

document.querySelector(".header_bar").addEventListener("click", function(event) {
  if (event.target.tagName !== "BUTTON") return;

  const buttonText = event.target.textContent.trim();
  const extensionsVisible = ["Chat", "Default", "Notebook"].includes(buttonText);
  const chatVisible = buttonText === "Chat";
  const showControlsChecked = document.querySelector("#show-controls input").checked;
  const extensions = document.querySelector("#extensions");

  if (extensionsVisible) {
    if (extensions) {
      extensions.style.display = "flex";
    }

    this.style.marginBottom = chatVisible ? "0px" : "19px";

    if (chatVisible && !showControlsChecked) {
      document.querySelectorAll(
        "#chat-tab > div > :nth-child(1), #chat-tab > div > :nth-child(3), #chat-tab > div > :nth-child(4), #extensions"
      ).forEach(element => {
        element.style.display = "none";
      });
    }

  } else {
    this.style.marginBottom = "19px";
    if (extensions) extensions.style.display = "none";
  }
});

//------------------------------------------------
// Keyboard shortcuts
//------------------------------------------------
let previousTabId = "chat-tab-button";
document.addEventListener("keydown", function(event) {

  // Stop generation on Esc pressed
  if (event.key === "Escape") {
    // Find the element with id 'stop' and click it
    var stopButton = document.getElementById("stop");
    if (stopButton) {
      stopButton.click();
    }
  }

  // Show chat controls on Ctrl + S
  else if (event.ctrlKey && event.key == "s") {
    event.preventDefault();

    var showControlsElement = document.getElementById("show-controls");
    if (showControlsElement && showControlsElement.childNodes.length >= 4) {
      showControlsElement.childNodes[3].click();

      var arr = document.getElementById("chat-input").childNodes[2].childNodes;
      arr[arr.length - 1].focus();
    }
  }

  // Regenerate on Ctrl + Enter
  else if (event.ctrlKey && event.key === "Enter") {
    event.preventDefault();
    document.getElementById("Regenerate").click();
  }

  // Continue on Alt + Enter
  else if (event.altKey && event.key === "Enter") {
    event.preventDefault();
    document.getElementById("Continue").click();
  }

  // Remove last on Ctrl + Shift + Backspace
  else if (event.ctrlKey && event.shiftKey && event.key === "Backspace") {
    event.preventDefault();
    document.getElementById("Remove-last").click();
  }

  // Copy last on Ctrl + Shift + K
  else if (event.ctrlKey && event.shiftKey && event.key === "K") {
    event.preventDefault();
    document.getElementById("Copy-last").click();
  }

  // Replace last on Ctrl + Shift + L
  else if (event.ctrlKey && event.shiftKey && event.key === "L") {
    event.preventDefault();
    document.getElementById("Replace-last").click();
  }

  // Impersonate on Ctrl + Shift + M
  else if (event.ctrlKey && event.shiftKey && event.key === "M") {
    event.preventDefault();
    document.getElementById("Impersonate").click();
  }

});

//------------------------------------------------
// Position the chat typing dots
//------------------------------------------------
typing = document.getElementById("typing-container");
typingParent = typing.parentNode;
typingSibling = typing.previousElementSibling;
typingSibling.insertBefore(typing, typingSibling.childNodes[2]);

//------------------------------------------------
// Chat scrolling
//------------------------------------------------
const targetElement = document.getElementById("chat").parentNode.parentNode.parentNode;
targetElement.classList.add("pretty_scrollbar");
targetElement.classList.add("chat-parent");
let isScrolled = false;

targetElement.addEventListener("scroll", function() {
  let diff = targetElement.scrollHeight - targetElement.clientHeight;
  if(Math.abs(targetElement.scrollTop - diff) <= 10 || diff == 0) {
    isScrolled = false;
  } else {
    isScrolled = true;
  }

  doSyntaxHighlighting();

});

// Create a MutationObserver instance
const observer = new MutationObserver(function(mutations) {
  updateCssProperties();

  if (targetElement.classList.contains("_generating")) {
    typing.parentNode.classList.add("visible-dots");
    document.getElementById("stop").style.display = "flex";
    document.getElementById("Generate").style.display = "none";
  } else {
    typing.parentNode.classList.remove("visible-dots");
    document.getElementById("stop").style.display = "none";
    document.getElementById("Generate").style.display = "flex";
  }


  doSyntaxHighlighting();

  if(!isScrolled) {
    targetElement.scrollTop = targetElement.scrollHeight;
  }

});

// Configure the observer to watch for changes in the subtree and attributes
const config = {
  childList: true,
  subtree: true,
  characterData: true,
  attributeOldValue: true,
  characterDataOldValue: true
};

// Start observing the target element
observer.observe(targetElement, config);

//------------------------------------------------
// Handle syntax highlighting / LaTeX
//------------------------------------------------
function isElementVisibleOnScreen(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.left < window.innerWidth &&
    rect.right > 0 &&
    rect.top < window.innerHeight &&
    rect.bottom > 0
  );
}

function getVisibleMessagesIndexes() {
  const elements = document.querySelectorAll(".message-body");
  const visibleIndexes = [];

  elements.forEach((element, index) => {
    if (isElementVisibleOnScreen(element) && !element.hasAttribute("data-highlighted")) {
      visibleIndexes.push(index);
    }
  });

  return visibleIndexes;
}

function doSyntaxHighlighting() {
  const indexes = getVisibleMessagesIndexes();
  const elements = document.querySelectorAll(".message-body");

  if (indexes.length > 0) {
    observer.disconnect();

    indexes.forEach((index) => {
      const element = elements[index];

      // Tag this element to prevent it from being highlighted twice
      element.setAttribute("data-highlighted", "true");

      // Perform syntax highlighting
      const codeBlocks = element.querySelectorAll("pre code");

      codeBlocks.forEach((codeBlock) => {
        hljs.highlightElement(codeBlock);
      });

      renderMathInElement(element, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true },
        ],
      });
    });

    observer.observe(targetElement, config);
  }
}

//------------------------------------------------
// Add some scrollbars
//------------------------------------------------
const textareaElements = document.querySelectorAll(".add_scrollbar textarea");
for(i = 0; i < textareaElements.length; i++) {
  textareaElements[i].classList.remove("scroll-hide");
  textareaElements[i].classList.add("pretty_scrollbar");
  textareaElements[i].style.resize = "none";
}

//------------------------------------------------
// Remove some backgrounds
//------------------------------------------------
const noBackgroundelements = document.querySelectorAll(".no-background");
for(i = 0; i < noBackgroundelements.length; i++) {
  noBackgroundelements[i].parentNode.style.border = "none";
  noBackgroundelements[i].parentNode.parentNode.parentNode.style.alignItems = "center";
}

const slimDropdownElements = document.querySelectorAll(".slim-dropdown");
for (i = 0; i < slimDropdownElements.length; i++) {
  const parentNode = slimDropdownElements[i].parentNode;
  parentNode.style.background = "transparent";
  parentNode.style.border = "0";
}

//------------------------------------------------
// Create the hover menu in the chat tab
// The show/hide events were adapted from:
// https://github.com/SillyTavern/SillyTavern/blob/6c8bd06308c69d51e2eb174541792a870a83d2d6/public/script.js
//------------------------------------------------
var buttonsInChat = document.querySelectorAll("#chat-tab #chat-buttons button");
var button = document.getElementById("hover-element-button");
var menu = document.getElementById("hover-menu");
var istouchscreen = (navigator.maxTouchPoints > 0) || "ontouchstart" in document.documentElement;

function showMenu() {
  menu.style.display = "flex"; // Show the menu
}

function hideMenu() {
  menu.style.display = "none"; // Hide the menu
  if (!istouchscreen) {
    document.querySelector("#chat-input textarea").focus(); // Focus on the chat input
  }
}

if (buttonsInChat.length > 0) {
  for (let i = buttonsInChat.length - 1; i >= 0; i--) {
    const thisButton = buttonsInChat[i];
    menu.appendChild(thisButton);

    thisButton.addEventListener("click", () => {
      hideMenu();
    });

    const buttonText = thisButton.textContent;
    const matches = buttonText.match(/(\(.*?\))/);

    if (matches && matches.length > 1) {
      // Apply the transparent-substring class to the matched substring
      const substring = matches[1];
      const newText = buttonText.replace(substring, `&nbsp;<span class="transparent-substring">${substring.slice(1, -1)}</span>`);
      thisButton.innerHTML = newText;
    }
  }
}

function isMouseOverButtonOrMenu() {
  return menu.matches(":hover") || button.matches(":hover");
}

button.addEventListener("mouseenter", function () {
  if (!istouchscreen) {
    showMenu();
  }
});

button.addEventListener("click", function () {
  if (menu.style.display === "flex") {
    hideMenu();
  }
  else {
    showMenu();
  }
});

// Add event listener for mouseleave on the button
button.addEventListener("mouseleave", function () {
  // Delay to prevent menu hiding when the mouse leaves the button into the menu
  setTimeout(function () {
    if (!isMouseOverButtonOrMenu()) {
      hideMenu();
    }
  }, 100);
});

// Add event listener for mouseleave on the menu
menu.addEventListener("mouseleave", function () {
  // Delay to prevent menu hide when the mouse leaves the menu into the button
  setTimeout(function () {
    if (!isMouseOverButtonOrMenu()) {
      hideMenu();
    }
  }, 100);
});

// Add event listener for click anywhere in the document
document.addEventListener("click", function (event) {
  const target = event.target;

  // Check if the click is outside the button/menu and the menu is visible
  if (!isMouseOverButtonOrMenu() && menu.style.display === "flex") {
    hideMenu();
  }

  if (event.target.classList.contains("pfp_character")) {
    toggleBigPicture();
  }

  // Handle sidebar clicks on mobile
  if (isMobile()) {
  // Check if the click did NOT originate from any of the specified toggle buttons or elements
    if (
      // target.closest("#navigation-toggle") !== navigationToggle &&
    target.closest("#past-chats-toggle") !== pastChatsToggle &&
    target.closest("#chat-controls-toggle") !== chatControlsToggle &&
    target.closest(".header_bar") !== headerBar &&
    target.closest("#past-chats-row") !== pastChatsRow &&
    target.closest("#chat-controls") !== chatControlsRow
    ) {
      handleIndividualSidebarClose(event);
    }
  }
});

//------------------------------------------------
// Relocate the "Show controls" checkbox
//------------------------------------------------
var elementToMove = document.getElementById("show-controls");
var parent = elementToMove.parentNode;
for (var i = 0; i < 2; i++) {
  parent = parent.parentNode;
}

parent.insertBefore(elementToMove, parent.firstChild);

//------------------------------------------------
// Position the chat input
//------------------------------------------------
document.getElementById("show-controls").parentNode.classList.add("chat-input-positioned");

//------------------------------------------------
// Focus on the chat input
//------------------------------------------------
const chatTextArea = document.getElementById("chat-input").querySelector("textarea");

function respondToChatInputVisibility(element, callback) {
  var options = {
    root: document.documentElement,
  };

  var observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      callback(entry.intersectionRatio > 0);
    });
  }, options);

  observer.observe(element);
}

function handleChatInputVisibilityChange(isVisible) {
  if (isVisible) {
    chatTextArea.focus();
  }
}

respondToChatInputVisibility(chatTextArea, handleChatInputVisibilityChange);

//------------------------------------------------
// Show enlarged character picture when the profile
// picture is clicked on
//------------------------------------------------
let bigPictureVisible = false;

function addBigPicture() {
  var imgElement = document.createElement("img");
  var timestamp = new Date().getTime();
  imgElement.src = "/file/cache/pfp_character.png?time=" + timestamp;
  imgElement.classList.add("bigProfilePicture");
  imgElement.addEventListener("load", function () {
    this.style.visibility = "visible";
  });
  imgElement.addEventListener("error", function () {
    this.style.visibility = "hidden";
  });

  var imgElementParent = document.getElementById("chat").parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode;
  imgElementParent.appendChild(imgElement);
}

function deleteBigPicture() {
  var bigProfilePictures = document.querySelectorAll(".bigProfilePicture");
  bigProfilePictures.forEach(function (element) {
    element.parentNode.removeChild(element);
  });
}

function toggleBigPicture() {
  if(bigPictureVisible) {
    deleteBigPicture();
    bigPictureVisible = false;
  } else {
    addBigPicture();
    bigPictureVisible = true;
  }
}

//------------------------------------------------
// Handle the chat input box growth
//------------------------------------------------
let currentChatInputHeight = 0;

// Update chat layout based on chat and input dimensions
function updateCssProperties() {
  const chatContainer = document.getElementById("chat").parentNode.parentNode.parentNode;
  const chatInputHeight = document.querySelector("#chat-input textarea").clientHeight;

  // Check if the chat container is visible
  if (chatContainer.clientHeight > 0) {
    const newChatHeight = `${chatContainer.parentNode.clientHeight - chatInputHeight + 40 - 100 - 20}px`;
    document.documentElement.style.setProperty("--chat-height", newChatHeight);
    document.documentElement.style.setProperty("--input-delta", `${chatInputHeight - 40}px`);

    // Adjust scrollTop based on input height change
    if (chatInputHeight !== currentChatInputHeight) {
      if (!isScrolled && chatInputHeight < currentChatInputHeight) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      } else {
        chatContainer.scrollTop += chatInputHeight - currentChatInputHeight;
      }

      currentChatInputHeight = chatInputHeight;
    }
  }
}

// Observe textarea size changes and call update function
new ResizeObserver(updateCssProperties).observe(document.querySelector("#chat-input textarea"));

// Handle changes in window size
window.addEventListener("resize", updateCssProperties);

//------------------------------------------------
// Focus on the rename text area when it becomes visible
//------------------------------------------------
const renameTextArea = document.getElementById("rename-row").querySelector("textarea");

function respondToRenameVisibility(element, callback) {
  var options = {
    root: document.documentElement,
  };

  var observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      callback(entry.intersectionRatio > 0);
    });
  }, options);

  observer.observe(element);
}


function handleVisibilityChange(isVisible) {
  if (isVisible) {
    renameTextArea.focus();
  }
}

respondToRenameVisibility(renameTextArea, handleVisibilityChange);

//------------------------------------------------
// Adjust the chat tab margin if no extension UI
// is present at the bottom
//------------------------------------------------

if (document.getElementById("extensions") === null) {
  document.getElementById("chat-tab").style.marginBottom = "-29px";
}

//------------------------------------------------
// Focus on the chat input after starting a new chat
//------------------------------------------------

document.querySelectorAll(".focus-on-chat-input").forEach(element => {
  element.addEventListener("click", function() {
    document.querySelector("#chat-input textarea").focus();
  });
});

//------------------------------------------------
// Fix a border around the "past chats" menu
//------------------------------------------------
document.getElementById("past-chats").parentNode.style.borderRadius = "0px";

//------------------------------------------------
// Allow the character dropdown to coexist at the
// Chat tab and the Parameters > Character tab
//------------------------------------------------

const headerBar = document.querySelector(".header_bar");
let originalParent;
let originalIndex; // To keep track of the original position
let movedElement;

function moveToChatTab() {
  const characterMenu = document.getElementById("character-menu");
  const grandParent = characterMenu.parentElement.parentElement;

  // Save the initial location for the character dropdown
  if (!originalParent) {
    originalParent = grandParent.parentElement;
    originalIndex = Array.from(originalParent.children).indexOf(grandParent);
    movedElement = grandParent;
  }

  // Do not show the Character dropdown in the Chat tab when "instruct" mode is selected
  const instructRadio = document.querySelector("#chat-mode input[value=\"instruct\"]");
  if (instructRadio && instructRadio.checked) {
    grandParent.style.display = "none";
  }

  grandParent.children[0].style.minWidth = "100%";

  const chatControlsFirstChild = document.querySelector("#chat-controls").firstElementChild;
  const newParent = chatControlsFirstChild;
  let newPosition = newParent.children.length - 2;

  newParent.insertBefore(grandParent, newParent.children[newPosition]);
  document.getElementById("save-character").style.display = "none";
}

function restoreOriginalPosition() {
  if (originalParent && movedElement) {
    if (originalIndex >= originalParent.children.length) {
      originalParent.appendChild(movedElement);
    } else {
      originalParent.insertBefore(movedElement, originalParent.children[originalIndex]);
    }

    document.getElementById("save-character").style.display = "";
    movedElement.style.display = "";
    movedElement.children[0].style.minWidth = "";
  }
}

headerBar.addEventListener("click", (e) => {
  if (e.target.tagName === "BUTTON") {
    const tabName = e.target.textContent.trim();
    if (tabName === "Chat") {
      moveToChatTab();
    } else {
      restoreOriginalPosition();
    }
  }
});

//------------------------------------------------
// Add a confirmation dialog when leaving the page
// Useful to avoid data loss
//------------------------------------------------
window.addEventListener("beforeunload", function (event) {
  // Cancel the event
  event.preventDefault();
  // Chrome requires returnValue to be set
  event.returnValue = "";
});

moveToChatTab();

//------------------------------------------------
// Buttons to toggle the sidebars
//------------------------------------------------

const leftArrowSVG = `<svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 0 24 24" width="48px" fill="#FFFFFF">
    <path d="M0 0h24v24H0z" fill="none"/>
    <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
  </svg>`;

const rightArrowSVG = `
  <svg xmlns="http://www.w3.org/2000/svg" height="48px" viewBox="0 0 24 24" width="48px" fill="#FFFFFF">
    <path d="M0 0h24v24H0z" fill="none"/>
    <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
  </svg>`;
const outputOnSVG =`<svg width="47" height="39" viewBox="0 0 47 39" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<mask id="mask0_8163_427" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="47" height="39">
<rect width="47" height="39" fill="url(#pattern0_8163_427)"/>
</mask>
<g mask="url(#mask0_8163_427)">
<rect x="5" y="-0.975098" width="42" height="39.975" fill="white"/>
</g>
<ellipse cx="33" cy="19.5" rx="10" ry="9.5" fill="#416BCF"/>
<defs>
<pattern id="pattern0_8163_427" patternContentUnits="objectBoundingBox" width="1" height="1">
<use xlink:href="#image0_8163_427" transform="matrix(0.00195312 0 0 0.00235377 0 -0.102564)"/>
</pattern>
<image id="image0_8163_427" width="512" height="512" xlink:href="data:image/png;base64,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"/>
</defs>
</svg>
`;
const outputOffSVG = `<svg width="47" height="40" viewBox="0 0 47 40" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<mask id="mask0_8162_424" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="47" height="40">
<rect width="47" height="40" transform="matrix(-1 0 0 1 47 0)" fill="url(#pattern0_8162_424)"/>
</mask>
<g mask="url(#mask0_8162_424)">
<rect width="47" height="40" fill="white"/>
</g>
<ellipse cx="15" cy="20" rx="9" ry="8" fill="#FFFEFE"/>
<defs>
<pattern id="pattern0_8162_424" patternContentUnits="objectBoundingBox" width="1" height="1">
<use xlink:href="#image0_8162_424" transform="matrix(0.00195312 0 0 0.00229492 0 -0.0875)"/>
</pattern>
<image id="image0_8162_424" width="512" height="512" xlink:href="data:image/png;base64,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"/>
</defs>
</svg>


`;

const hamburgerMenuSVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-hamburger-menu">
  <line x1="3" y1="12" x2="21" y2="12"></line>
  <line x1="3" y1="6" x2="21" y2="6"></line>
  <line x1="3" y1="18" x2="21" y2="18"></line>
</svg>`;

const closeMenuSVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-close-menu">
  <line x1="18" y1="6" x2="6" y2="18"></line>
  <line x1="6" y1="6" x2="18" y2="18"></line>
</svg>`;

const chatTab = document.getElementById("chat-tab");
const pastChatsRow = document.getElementById("past-chats-row");
const chatControlsRow = document.getElementById("chat-controls");
const outputOffToggle = document.getElementById("toggle-off");
const outputOnToggle = document.getElementById("toggle-on");
const svgDataOnUrl = 'file/cache/toggle-on.png';
const svgDataOffUrl = 'file/cache/toggle-off.png';
outputOffToggle.style.backgroundImage = `url("${svgDataOffUrl}")`;
outputOnToggle.style.backgroundImage = `url("${svgDataOnUrl}")`;
if (chatTab) {
  // Create past-chats-toggle div
  const pastChatsToggle = document.createElement("div");
  pastChatsToggle.id = "past-chats-toggle";
  pastChatsToggle.innerHTML = leftArrowSVG; // Set initial icon to left arrow
  pastChatsToggle.classList.add("past-chats-open"); // Set initial position

  // Create chat-controls-toggle div
  const chatControlsToggle = document.createElement("div");
  chatControlsToggle.id = "chat-controls-toggle";
  chatControlsToggle.innerHTML = rightArrowSVG; // Set initial icon to right arrow
  chatControlsToggle.classList.add("chat-controls-open"); // Set initial position

  // Append both elements to the chat-tab
  chatTab.appendChild(pastChatsToggle);
  chatTab.appendChild(chatControlsToggle);
}

// Create navigation toggle div
// const navigationToggle = document.createElement("div");
// navigationToggle.id = "navigation-toggle";
// navigationToggle.innerHTML = leftArrowSVG; // Set initial icon to right arrow
// navigationToggle.classList.add("navigation-left"); // Set initial position
// headerBar.appendChild(navigationToggle);

// Retrieve the dynamically created toggle buttons
const pastChatsToggle = document.getElementById("past-chats-toggle");
const chatControlsToggle = document.getElementById("chat-controls-toggle");
const leftSideToggle = document.getElementById("left-side");
const outputText = document.getElementById("output-text");

function handleIndividualSidebarClose(event) {
  const target = event.target;

  // Close navigation bar if click is outside and it is open
  // if (!headerBar.contains(target) && !headerBar.classList.contains("sidebar-hidden")) {
  //   toggleSidebar(headerBar, navigationToggle, true);
  // }

  // Close past chats row if click is outside and it is open
  if (!pastChatsRow.contains(target) && !pastChatsRow.classList.contains("sidebar-hidden")) {
    toggleSidebar(pastChatsRow, pastChatsToggle, true);
  }

  // Close chat controls row if click is outside and it is open
  if (!chatControlsRow.contains(target) && !chatControlsRow.classList.contains("sidebar-hidden")) {
    toggleSidebar(chatControlsRow, chatControlsToggle, true);
  }
}

function toggleSidebar(sidebar, toggle, forceClose = false) {
  const isCurrentlyHidden = sidebar.classList.contains("sidebar-hidden");
  const shouldClose = !isCurrentlyHidden;

  // Apply visibility classes
  sidebar.classList.toggle("sidebar-hidden", shouldClose);
  sidebar.classList.toggle("sidebar-shown", !shouldClose);

  if (sidebar === headerBar) {
    // Special handling for header bar
    document.documentElement.style.setProperty("--header-width", shouldClose ? "0px" : "112px");
    pastChatsRow.classList.toggle("negative-header", shouldClose);
    pastChatsToggle.classList.toggle("negative-header", shouldClose);
    toggle.innerHTML = shouldClose ? hamburgerMenuSVG : closeMenuSVG;
  } else if (sidebar === pastChatsRow) {
    // Past chats sidebar
    pastChatsToggle.classList.toggle("past-chats-closed", shouldClose);
    pastChatsToggle.classList.toggle("past-chats-open", !shouldClose);
    if(!shouldClose){
      pastChatsToggle.classList.remove("past-chat-move");
      pastChatsToggle.innerHTML = leftArrowSVG;
    }else{
      pastChatsToggle.classList.add("past-chat-move");
      pastChatsToggle.innerHTML = rightArrowSVG;
    }
  } else if (sidebar === chatControlsRow) {
    // Chat controls sidebar
    toggle.classList.toggle("chat-controls-closed", shouldClose);
    toggle.classList.toggle("chat-controls-open", !shouldClose);
    toggle.innerHTML = shouldClose ? leftArrowSVG : rightArrowSVG;
    if(!shouldClose){
      outputOnToggle.classList.add("right-side-move");
      outputOffToggle.classList.add("right-side-move");
      outputText.classList.remove("output-back");
    }else{
      outputOffToggle.classList.remove("right-side-move");
      outputOnToggle.classList.remove("right-side-move");
      outputText.classList.add("output-back");
    }
  }

}

// Function to check if the device is mobile
function isMobile() {
  return window.innerWidth <= 924;
}

// Function to initialize sidebars
function initializeSidebars() {
  // Hide pastChatsRow (chat sidebar) and other sidebars by default
  [pastChatsRow].forEach((sidebar) => {
    sidebar.classList.add("sidebar-hidden");
    sidebar.classList.remove("sidebar-shown");
  });

  // Update the toggle buttons to match the closed state
  pastChatsToggle.classList.add("past-chats-closed");
  pastChatsToggle.classList.remove("past-chats-open");
  pastChatsToggle.innerHTML = rightArrowSVG;
  if(isMobile()) {
    outputText.classList.add("output-back");
    outputOnToggle.classList.remove("right-side-move");
    outputOffToggle.classList.remove("right-side-move");
  } else {
    outputText.classList.remove("output-back");
    outputOnToggle.classList.add("right-side-move");
    outputOffToggle.classList.add("right-side-move");
  }
  pastChatsToggle.classList.add("past-chat-move");
  chatControlsToggle.classList.remove("chat-controls-closed");
  chatControlsToggle.classList.add("chat-controls-open");
  chatControlsToggle.innerHTML = rightArrowSVG;

  // navigationToggle.innerHTML = hamburgerMenuSVG;

  // Ensure header width is reset
  document.documentElement.style.setProperty("--header-width", "0px");
}

// Run the initializer when the page loads
initializeSidebars();

outputOffToggle.addEventListener("click", () => {
  outputOffToggle.classList.add("hideCurOutput");
  outputOnToggle.classList.remove("hideCurOutput");
});
outputOnToggle.addEventListener("click", () => {
  outputOffToggle.classList.remove("hideCurOutput");
  outputOnToggle.classList.add("hideCurOutput");
});
// Add click event listeners to toggle buttons
pastChatsToggle.addEventListener("click", () => {
  toggleSidebar(pastChatsRow, pastChatsToggle);
});

chatControlsToggle.addEventListener("click", () => {
  toggleSidebar(chatControlsRow, chatControlsToggle);
});

// navigationToggle.addEventListener("click", () => {
//   toggleSidebar(headerBar, navigationToggle);
// });

//------------------------------------------------
// Fixes #chat-input textarea height issue
// for devices with width <= 924px
//------------------------------------------------




if (isMobile()) {
  const textarea = document.querySelector("#chat-input textarea");
  if (textarea) {
    // Simulate adding and removing a newline
    textarea.value += "\n";
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
    textarea.value = textarea.value.slice(0, -1);
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  chatControlsToggle.classList.remove("chat-controls-open");
  chatControlsToggle.classList.add("chat-controls-closed");
  chatControlsToggle.innerHTML = leftArrowSVG;
  chatControlsRow.classList.add("sidebar-hidden");
  chatControlsRow.classList.remove("sidebar-shown");

  textarea.addEventListener('focus', function() {
    setTimeout(() => {
      this.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
  });
}

//------------------------------------------------
// Create a top navigation bar on mobile
//------------------------------------------------

function createMobileTopBar() {
  const chatTab = document.getElementById("chat-tab");

  // Only create the top bar if it doesn't already exist
  if (chatTab && !chatTab.querySelector(".mobile-top-bar")) {
    const topBar = document.createElement("div");
    topBar.classList.add("mobile-top-bar");

    // Insert the top bar as the first child of chat-tab
    chatTab.appendChild(topBar);
  }
}

// createMobileTopBar();

// particlesJS("chat", {"particles":{"number":{"value":80,"density":{"enable":true,"value_area":500}},"color":{"value":"#ffffff"},"shape":{"type":"polygon","stroke":{"width":0,"color":"#000000"},"polygon":{"nb_sides":5},"image":{"src":"img/github.svg","width":100,"height":100}},"opacity":{"value":0.5,"random":false,"anim":{"enable":false,"speed":1,"opacity_min":0.1,"sync":false}},"size":{"value":2,"random":true,"anim":{"enable":false,"speed":40,"size_min":0.1,"sync":false}},"line_linked":{"enable":true,"distance":150,"color":"#988bfa","opacity":0.4,"width":1},"move":{"enable":true,"speed":6,"direction":"none","random":false,"straight":false,"out_mode":"out","bounce":false,"attract":{"enable":false,"rotateX":600,"rotateY":1200}}},"interactivity":{"detect_on":"canvas","events":{"onhover":{"enable":true,"mode":"grab"},"onclick":{"enable":true,"mode":"push"},"resize":true},"modes":{"grab":{"distance":150,"line_linked":{"opacity":1}},"bubble":{"distance":400,"size":40,"duration":2,"opacity":8,"speed":3},"repulse":{"distance":200,"duration":0.4},"push":{"particles_nb":4},"remove":{"particles_nb":2}}},"retina_detect":true});var count_particles, stats, update; stats = new Stats; stats.setMode(0); stats.domElement.style.position = 'absolute'; stats.domElement.style.left = '0px'; stats.domElement.style.top = '0px'; document.body.appendChild(stats.domElement); count_particles = document.querySelector('.js-count-particles'); update = function() { stats.begin(); stats.end(); if (window.pJSDom[0].pJS.particles && window.pJSDom[0].pJS.particles.array) { count_particles.innerText = window.pJSDom[0].pJS.particles.array.length; } requestAnimationFrame(update); }; requestAnimationFrame(update);;
