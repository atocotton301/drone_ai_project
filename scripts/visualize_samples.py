import os

def visualize_samples(dataset_dir, output_dir):
    print(f"Visualizing samples from {dataset_dir}")
    os.makedirs(output_dir, exist_ok=True)
    # 이미지에 Bounding Box 및 클래스 이름 렌더링 로직 (Mock)
    print(f"Sample images with bounding boxes saved to {output_dir}")

if __name__ == "__main__":
    visualize_samples("datasets/sample", "outputs/sample_labels")
