import kagglehub
import torch
from torch.utils.data import WeightedRandomSampler, random_split, DataLoader
from torchvision import datasets, transforms
from collections import Counter
import pandas as pd
import os
import shutil
import matplotlib.pyplot as plt
def download_and_prepare_data(wolf):
    """
    Downloads and prepares the Stanford Dogs and Wolves datasets.
    Moves wolf images into the Stanford Dogs directory under a 'wolf' class.
    """
    # Download datasets
    path_stanford_dogs = kagglehub.dataset_download("jessicali9530/stanford-dogs-dataset")

    # Define directories
    dogs_dir = os.path.join(path_stanford_dogs, "images/images")
    if wolf:

        path_wolfs = kagglehub.dataset_download("harishvutukuri/dogs-vs-wolves")
        wolves_dir = os.path.join(path_wolfs, "data", "wolves")
        wolf_class_dir = os.path.join(dogs_dir, "wolf")
        # Integrate wolves into the dogs dataset
        os.makedirs(wolf_class_dir, exist_ok=True)
        for file_name in os.listdir(wolves_dir):
            src_path = os.path.join(wolves_dir, file_name)
            dest_path = os.path.join(wolf_class_dir, file_name)
            if os.path.isfile(src_path):
                shutil.move(src_path, dest_path)

    return dogs_dir

def create_sampler(dataset):
    """
    Creates a WeightedRandomSampler for handling class imbalance.

    Args:
        dataset: The dataset for which the sampler is created.

    Returns:
        sampler: A WeightedRandomSampler object.
        weight_df: A DataFrame containing class weights and counts.
    """
    class_counts = Counter(dataset.dataset.targets[i] for i in dataset.indices)
    all_classes = range(len(dataset.dataset.classes))

    for cls in all_classes:
        if cls not in class_counts:
            class_counts[cls] = 0

    class_weights = {cls: 1.0 / count if count > 0 else 0 for cls, count in class_counts.items()}
    sample_weights = [class_weights[dataset.dataset.targets[i]] for i in dataset.indices]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)

    weight_df = pd.DataFrame({
        'Class': dataset.dataset.classes,
        'Count': [class_counts[cls] for cls in all_classes],
        'Weight': [class_weights[cls] for cls in all_classes]
    })

    return sampler, weight_df

def get_data(batch_size=128, imbalance_handling=True,wolf = True,workers=4):
    """
    Prepares the dataset and dataloaders with optional imbalance handling.

    Args:
        batch_size: The batch size for DataLoaders.
        imbalance_handling: Whether to apply imbalance handling with a sampler.

    Returns:
        train_loader, val_loader, test_loader: DataLoaders for training, validation, and testing.
        classes_weights: A DataFrame with class weights and counts.
    """
    # Download and prepare data
    dogs_dir = download_and_prepare_data(wolf)

    # Define transforms
    transform = transforms.Compose([
        transforms.Resize((331, 331)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Prepare datasets
    dog_dataset = datasets.ImageFolder(dogs_dir, transform=transform)
    train_size = int(0.7 * len(dog_dataset))
    val_size = int(0.15 * len(dog_dataset))
    test_size = len(dog_dataset) - train_size - val_size
    train_dataset, val_dataset, test_dataset = random_split(dog_dataset, [train_size, val_size, test_size])

    # Handle imbalance with a sampler
    if imbalance_handling:
        train_sampler, classes_weights = create_sampler(train_dataset)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=train_sampler,drop_last=True,num_workers=workers)
    else:
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,drop_last=True,num_workers=workers)
        classes_weights = None

    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False,drop_last=True,num_workers=workers)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False,drop_last=True,num_workers=workers)

    return train_loader, val_loader, test_loader, classes_weights



def plot_training_history(history):
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss', color='blue', linewidth=1)
    plt.plot(history['val_loss'], label='Validation Loss', color='red', linewidth=1)

    plt.title('Training Loss Over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid()


    plt.subplot(1, 2, 2)
    plt.plot(history['val_f1'], label='Validation F1-Score', color='green', linewidth=2)
    plt.title('Validation F1-Score Over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('F1-Score')
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()