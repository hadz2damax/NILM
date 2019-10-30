from __future__ import print_function, division
from warnings import warn
import pandas as pd
import numpy as np
import json
from nilmtk.disaggregate import Disaggregator
import os

class Mean(Disaggregator):
	"""Mean algorithm"""
	def __init__(self, params):
		"""Initializes the model with the specicied parameters"""
		self.model = {}
		self.MODEL_NAME = 'Mean'  # Add the name for the algorithm
		self.save_model_path = params.get('save-model-path', None)
		self.load_model_path = params.get('pretrained-model-path',None)

		# The flag variable to train chunk wise
		self.chunk_wise_training = params.get('chunk_wise_training', False)
		if self.load_model_path:
			self.load_model(self.load_model_path)

	def partial_fit(self, train_main, train_appliances, **load_kwargs):
		"""Fits the model

		Attributes
		----------
		train_main: List of mains dataframes
		train_appliances: List of tuples, where each tuple is (appliance_name, List of appliance data frames)
		"""

		for app_name, power in train_appliances:
			print ("Training %s in %s model".format(app_name, self.MODEL_NAME), end="\r")
			power_ = pd.concat(power, axis=0)
			app_dict = self.model.get(app_name, {'sum': 0,'n_elem': 0})
			app_dict['sum'] += int(np.nansum(power_.values))
			app_dict['n_elem'] += len(power_[~np.isnan(power_)])
			self.model[app_name] = app_dict
		if self.save_model_path:
			self.save_model(self.save_model_path)

	def disaggregate_chunk(self, test_mains):
		"""Returns the predictions

		Attributes
		----------
		test_mains: List of mains dataframes

		Returns
		-------
		For each mains dataframe, it returns the predictions dataframe. The predictions dataframe has appliances as columns and has a predictions corresponding to each row of the mains dataframe.
		"""
		
		test_predictions_list = []
		for test_df in test_mains:
			appliance_powers = pd.DataFrame()
			for i, app_name in enumerate(self.model):
				app_model = self.model[app_name]
				predicted_power = [app_model['sum'] / app_model['n_elem']] * test_df.shape[0]
				appliance_powers[app_name] = pd.Series(predicted_power, index=test_df.index, name=i)
			test_predictions_list.append(appliance_powers)
		return test_predictions_list

	def save_model(self, folder_name):
		string_to_save = json.dumps(self.model)
		os.makedirs(folder_name, exist_ok=True)
		with open(os.path.join(folder_name, "model.txt") ,"w") as f:
			f.write(string_to_save)

	def load_model(self, folder_name):
		with open(os.path.join(folder_name, "model.txt") ,"w") as f:
			model_string = f.read().strip()
			self.model = json.loads(model_string)
