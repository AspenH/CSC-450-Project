"""
	Project: Project Slate
	Programmed by: Slate Hayes

Liscense:
Copyright (c) 2017, FandRec Dev Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
	* Redistributions of source code must retain the above copyright
	  notice, this list of conditions and the following disclaimer.
	* Redistributions in binary form must reproduce the above copyright
	  notice, this list of conditions and the following disclaimer in the
	  documentation and/or other materials provided with the distribution.
	* Neither the name of the FandRec Dev Team nor the
	  names of its contributors may be used to endorse or promote products
	  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL FandRec Dev Team BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import ujson

class CVO:
	"""
	Programmed by: Slate Hayes
	Description: Class that handles the interactions with the CVO File received from CoMPES
	Notes:
		1. Is used slate.py program.
	"""

	def __init__(self, cvo_string):
		"""
		Programmed by: Slate Hayes
		Description: Sets the cvo member to the json equivalent of what was passed into it
		"""

		self.cvo = ujson.loads(cvo_string)

	def get_acus(self):
		"""
		Programmed by: Slate Hayes
		Description: Returns the acus that were found in the cvo file that was passed in
		"""

		return self.cvo

	def get_acu(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the and acu based off of the passed in acu id
		"""

		if acu_id not in self.cvo:
			raise AttributeError
		else:
			return self.cvo[acu_id]

	def get_acu_id(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the acu id of the current acu based on the acu id
		"""

		acu = self.get_acu(acu_id)
		if 'ACU ID' not in acu.keys():
			raise AttributeError
		else:
			return acu['ACU ID']

	def get_acu_classification(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the classification of the current acu based on the acu id
		"""

		acu = self.get_acu(acu_id)
		if 'Classification' not in acu.keys():
			raise AttributeError
		else:
			return acu['Classification']

	def get_acu_states(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the states of the current acu based on the acu id
		"""

		acu = self.get_acu(acu_id)
		if 'Defined States' not in acu.keys():
			raise AttributeError
		else:
			return acu['Defined States']

	def get_acu_actions(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the actions of the current acu based on the acu id
		"""

		acu = self.get_acu(acu_id)
		if 'Actions' not in acu.keys():
			raise AttributeError
		else:
			return acu['Actions']

	def get_acu_semlinks(self, acu_id):
		"""
		Programmed by: Slate Hayes
		Description: Returns the Sematic links of the current acu based on the acu id
		"""
		
		acu = self.get_acu(acu_id)
		if 'Semantic Links' not in acu.keys():
			raise AttributeError
		else:
			return acu['Semantic Links']
