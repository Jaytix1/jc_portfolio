import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Define the model (same as before)
class DigitClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(784, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, 10)
    
    def forward(self, x):
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Training function
def train_one_epoch(model, train_loader, criterion, optimizer):
    model.train()
    total_loss = 0
    
    for batch_idx, (data, target) in enumerate(train_loader):
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        if batch_idx % 100 == 0:
            print(f'  Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}')
    
    avg_loss = total_loss / len(train_loader)
    print(f'  Average Loss: {avg_loss:.4f}')

# Testing function
def test(model, test_loader):
    model.eval()
    correct = 0
    total = 0
    
    with torch.no_grad():
        for data, target in test_loader:
            output = model(data)
            _, predicted = torch.max(output, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
    
    accuracy = 100 * correct / total
    print(f'  Accuracy: {accuracy:.2f}%\n')
    return accuracy

def continue_training(additional_epochs=5):
    print("=== Continuing Training ===\n")
    
    # Load existing model
    model = DigitClassifier()
    model.load_state_dict(torch.load('mnist_model.pth'))
    print("✓ Loaded existing model\n")
    
    # Prepare data
    transform = transforms.ToTensor()
    print("Loading MNIST dataset...")
    train_data = datasets.MNIST(root='data', train=True, download=True, transform=transform)
    test_data = datasets.MNIST(root='data', train=False, download=True, transform=transform)
    
    train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=64, shuffle=False)
    print("✓ Data loaded\n")
    
    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # Test current accuracy
    print("Current accuracy BEFORE additional training:")
    test(model, test_loader)
    
    # Train more
    print(f"Training for {additional_epochs} additional epochs...\n")
    for epoch in range(additional_epochs):
        print(f'Epoch {epoch+1}/{additional_epochs}')
        train_one_epoch(model, train_loader, criterion, optimizer)
        test(model, test_loader)
    
    # Save improved model
    torch.save(model.state_dict(), 'mnist_model.pth')
    print("✓ Saved improved model to 'mnist_model.pth'!")

if __name__ == "__main__":
    # Change this number to train for more/fewer epochs
    continue_training(additional_epochs=5)