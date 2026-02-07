import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt

# ============ PART 1: DEFINE THE MODEL ============
class DigitClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()           # Converts 28x28 to 784
        self.fc1 = nn.Linear(784, 128)        # First layer: 784 → 128
        self.relu = nn.ReLU()                 # Activation function
        self.fc2 = nn.Linear(128, 10)         # Output layer: 128 → 10 digits
    
    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# ============ PART 2: TRAINING FUNCTION ============
def train_one_epoch(model, train_loader, criterion, optimizer):
    model.train()  # Set to training mode
    total_loss = 0
    
    for batch_idx, (data, target) in enumerate(train_loader):
        # Reset gradients
        optimizer.zero_grad()
        
        # Forward pass
        output = model(data)
        
        # Calculate loss
        loss = criterion(output, target)
        
        # Backward pass
        loss.backward()
        
        # Update weights
        optimizer.step()
        
        total_loss += loss.item()
        
        # Print progress every 100 batches
        if batch_idx % 100 == 0:
            print(f'  Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}')
    
    avg_loss = total_loss / len(train_loader)
    print(f'  Average Loss: {avg_loss:.4f}')

# ============ PART 3: TESTING FUNCTION ============
def test(model, test_loader):
    model.eval()  # Set to evaluation mode
    correct = 0
    total = 0
    
    with torch.no_grad():  # Don't calculate gradients
        for data, target in test_loader:
            output = model(data)
            
            # Get predicted digit (highest score)
            _, predicted = torch.max(output, 1)
            
            total += target.size(0)
            correct += (predicted == target).sum().item()
    
    accuracy = 100 * correct / total
    print(f'  Accuracy: {accuracy:.2f}%\n')
    return accuracy

# ============ PART 4: VISUALIZATION (OPTIONAL) ============
def show_predictions(model, test_data, num_images=5):
    """Show some test images with predictions"""
    model.eval()
    
    fig, axes = plt.subplots(1, num_images, figsize=(12, 3))
    
    for i in range(num_images):
        # Get a random image
        image, label = test_data[i]
        
        # Make prediction
        with torch.no_grad():
            output = model(image.unsqueeze(0))  # Add batch dimension
            _, predicted = torch.max(output, 1)
        
        # Display
        axes[i].imshow(image.squeeze(), cmap='gray')
        axes[i].set_title(f'True: {label}\nPred: {predicted.item()}')
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.savefig('predictions.png')
    print("Saved predictions to 'predictions.png'")

# ============ PART 5: MAIN EXECUTION ============
def main():
    print("Starting MNIST Digit Classifier Training...\n")
    
    # Set random seed for reproducibility
    torch.manual_seed(42)
    
    # Prepare data transformations
    transform = transforms.ToTensor()
    
    # Download and load datasets
    print("Downloading MNIST dataset...")
    train_data = datasets.MNIST(root='data', train=True, download=True, transform=transform)
    test_data = datasets.MNIST(root='data', train=False, download=True, transform=transform)
    
    # Create data loaders
    train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=64, shuffle=False)
    print(f"Loaded {len(train_data)} training images and {len(test_data)} test images\n")
    
    # Create model, loss function, and optimizer
    model = DigitClassifier()
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Display model architecture
    print("Model Architecture:")
    print(model)
    print()
    
    # Training loop
    epochs = 10
    print(f"Training for {epochs} epochs...\n")
    
    for epoch in range(epochs):
        print(f'Epoch {epoch+1}/{epochs}')
        train_one_epoch(model, train_loader, criterion, optimizer)
        test(model, test_loader)
    
    # Save the trained model
    torch.save(model.state_dict(), 'mnist_model.pth')
    print("✓ Model saved as 'mnist_model.pth'")
    
    # Show some predictions
    print("\nGenerating prediction visualizations...")
    show_predictions(model, test_data, num_images=5)
    
    print("\nTraining complete!")
    print("\nTo use this model later:")
    print("  model = DigitClassifier()")
    print("  model.load_state_dict(torch.load('mnist_model.pth'))")

if __name__ == "__main__":
    main()

