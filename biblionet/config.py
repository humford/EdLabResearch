import yaml

with open("./config.yaml", "r") as yamlfile:
	config = yaml.load(yamlfile, Loader=yaml.FullLoader)