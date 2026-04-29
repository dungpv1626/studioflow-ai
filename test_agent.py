import sys, traceback, asyncio
sys.stdout.reconfigure(encoding='utf-8')

print("=== TEST KIE AI IMAGE GENERATION ===")
try:
    from skills.image_generation import generate_preset_image
    result = asyncio.run(generate_preset_image("social_post", output_path="output/test_kie.jpg"))
    print("OK!")
    print("Image URL:", result["image_url"])
    print("Task ID  :", result["task_id"])
    print("Saved    :", result["local_path"])
except Exception as e:
    traceback.print_exc()
