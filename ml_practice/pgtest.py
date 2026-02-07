import tkinter as tk
from PIL import Image, ImageDraw, ImageOps
import torch
from torchvision import transforms
from mnist_classifier import DigitClassifier

class DigitRecognizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Digit Recognizer")
        
        # Load the trained model
        self.model = DigitClassifier()
        self.model.load_state_dict(torch.load('mnist_model.pth'))
        self.model.eval()
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(root, width=280, height=280, bg='white', cursor='cross')
        self.canvas.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        # Create PIL image for drawing (higher resolution for better quality)
        self.image = Image.new('L', (280, 280), 'white')
        self.draw = ImageDraw.Draw(self.image)
        
        # Bind mouse events
        self.canvas.bind('<B1-Motion>', self.paint)
        
        # Prediction label
        self.prediction_label = tk.Label(root, text="Draw a digit (0-9)", font=('Arial', 20))
        self.prediction_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Buttons
        self.predict_btn = tk.Button(root, text="Predict", command=self.predict, 
                                     font=('Arial', 14), bg='#4CAF50', fg='white', width=12)
        self.predict_btn.grid(row=2, column=0, padx=5, pady=10)
        
        self.clear_btn = tk.Button(root, text="Clear", command=self.clear_canvas, 
                                   font=('Arial', 14), bg='#f44336', fg='white', width=12)
        self.clear_btn.grid(row=2, column=1, padx=5, pady=10)
        
        # Store last position for smoother drawing
        self.last_x, self.last_y = None, None
    
    def paint(self, event):
        """Draw on canvas as user moves mouse"""
        x, y = event.x, event.y
        
        # Draw thicker line by using circles
        r = 8  # Brush radius
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='black', outline='black')
        
        # Draw on PIL image too
        if self.last_x and self.last_y:
            self.draw.line([self.last_x, self.last_y, x, y], fill='black', width=r*2)
        self.draw.ellipse([x-r, y-r, x+r, y+r], fill='black')
        
        self.last_x, self.last_y = x, y
    
    def clear_canvas(self):
        """Clear the drawing"""
        self.canvas.delete('all')
        self.image = Image.new('L', (280, 280), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.prediction_label.config(text="Draw a digit (0-9)", fg='black')
        self.last_x, self.last_y = None, None
    
    def predict(self):
        """Run the drawing through the neural network"""
        # Reset last position
        self.last_x, self.last_y = None, None
        
        # Preprocess the image
        # 1. Resize to 28x28 (MNIST size)
        img_resized = self.image.resize((28, 28), Image.LANCZOS)
        
        # 2. Invert colors (MNIST is white digit on black background)
        img_inverted = ImageOps.invert(img_resized)
        
        # 3. Convert to tensor
        transform = transforms.ToTensor()
        img_tensor = transform(img_inverted).unsqueeze(0)  # Add batch dimension
        
        # 4. Run through model
        with torch.no_grad():
            output = self.model(img_tensor)
            probabilities = torch.softmax(output, 1)
            confidence, predicted = torch.max(probabilities, 1)
        
        # Display prediction
        digit = predicted.item()
        conf = confidence.item() * 100
        
        self.prediction_label.config(
            text=f"Prediction: {digit} ({conf:.1f}% confident)",
            fg='green' if conf > 70 else 'orange'
        )
        
        print(f"Predicted: {digit} with {conf:.1f}% confidence")
        
        # Show all probabilities (for debugging)
        print("\nAll probabilities:")
        for i, prob in enumerate(probabilities[0]):
            print(f"  {i}: {prob.item()*100:.2f}%")

def main():
    root = tk.Tk()
    app = DigitRecognizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()