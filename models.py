from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer


# Specify the model directory where you want to save the model
model_name = "facebook/m2m100_418M"
save_directory = "./m2m100_model"

# Download the tokenizer and model, and save them locally
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
tokenizer.save_pretrained(save_directory)

model = M2M100ForConditionalGeneration.from_pretrained(model_name)
model.save_pretrained(save_directory)

