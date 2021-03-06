# -*- coding: utf-8 -*-
'''
/***************************************************************************
 Paprika
								 A QGIS plugin
 perform the Paprika Method with QGIS
							  -------------------
		begin				: 2017-01-09
		git sha			  : $Format:%H$
		copyright			: (C) 2017 by SIG
		email				: ylecomte@sig.eu.com
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
'''
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QMessageBox
from PyQt4 import QtGui, uic, QtCore
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from A_propos import Ui_A_propos
from paprika_dockwidget import Ui_PaprikaDockWidgetBase
import os
import sys
from qgis.gui import *
from qgis.core import *
import webbrowser

import raster_extension
import Carte_P
import Carte_R
import Carte_I
import Carte_Ka
import Carte_Finale

class Paprika:
	'''QGIS Plugin Implementation.'''

	def __init__(self, iface):
		'''Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		'''
		# Save reference to the QGIS interface
		self.iface = iface

		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)

		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'Paprika_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)

			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)

		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&Paprika')
		# TODO: We are going to let the user set this up in a future iteration
		self.toolbar = self.iface.addToolBar(u'Paprika')
		self.toolbar.setObjectName(u'Paprika')

		#print "** INITIALIZING Paprika"

		self.pluginIsActive = False
		self.dockwidget = None


	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		'''Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		'''
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('Paprika', message)


	def add_action(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):
		'''Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		'''

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			self.toolbar.addAction(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action


	def initGui(self):
		'''Create the menu entries and toolbar icons inside the QGIS GUI.'''

		icon_path = ':/plugins/Paprika/icon.png'
		self.add_action(
			icon_path,
			text=self.tr(u'Paprika'),
			callback=self.run,
			parent=self.iface.mainWindow())
			

	#--------------------------------------------------------------------------

	def onClosePlugin(self):
		'''Cleanup necessary items here when plugin dockwidget is closed'''

		#print "** CLOSING Paprika"

		# disconnects
		self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

		# remove this statement if dockwidget is to remain
		# for reuse if plugin is reopened
		# Commented next statement since it causes QGIS crashe
		# when closing the docked window:
		# self.dockwidget = None

		self.pluginIsActive = False


	def unload(self):
		'''Removes the plugin menu item and icon from QGIS GUI.'''

		#print "** UNLOAD Paprika"

		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&Paprika'),
				action)
			self.iface.removeToolBarIcon(action)
		# remove the toolbar
		del self.toolbar

	#--------------------------------------------------------------------------
	def run(self):
		'''Run method that loads and starts the plugin'''
		
			
		if not self.pluginIsActive:
			self.pluginIsActive = True

			#print "** STARTING Paprika"

			# dockwidget may not exist if:
			#	first run of plugin
			#	removed on close (see self.onClosePlugin method)
			if self.dockwidget == None:
				# Create the dockwidget (after translation) and keep reference
				self.dockwidget = Ui_PaprikaDockWidgetBase()
			
			#connection des boutons
			QtCore.QObject.connect(self.dockwidget.pushButton_Aide, QtCore.SIGNAL("clicked ()"), self.open_help)
			QtCore.QObject.connect(self.dockwidget.pushButton_methodo, QtCore.SIGNAL("clicked ()"), self.download_methodo)
			QtCore.QObject.connect(self.dockwidget.pushButton_genere_guide, QtCore.SIGNAL("clicked ()"), self.lancer_genere_guide)
			QtCore.QObject.connect(self.dockwidget.pushButton_lancerCarteP, QtCore.SIGNAL("clicked ()"), self.lancer_carteP)
			QtCore.QObject.connect(self.dockwidget.pushButton_lancerCarteR, QtCore.SIGNAL("clicked ()"), self.lancer_carteR)
			QtCore.QObject.connect(self.dockwidget.pushButton_lancerCarteI, QtCore.SIGNAL("clicked ()"), self.lancer_carteI)
			QtCore.QObject.connect(self.dockwidget.pushButton_lancerCarteKa, QtCore.SIGNAL("clicked ()"), self.lancer_carteKa)
			QtCore.QObject.connect(self.dockwidget.pushButton_lancerCarteFinale, QtCore.SIGNAL("clicked ()"), self.lancer_carteFinale)
			QtCore.QObject.connect(self.dockwidget.toolButton_dossier_travail, QtCore.SIGNAL("clicked ()"), self.open_directory)
			QtCore.QObject.connect(self.dockwidget.pushButton_Apropos, QtCore.SIGNAL("clicked ()"),self.open_Apropos)		
			# connect to provide cleanup on closing of dockwidget
			self.dockwidget.closingPlugin.connect(self.onClosePlugin)

			# show the dockwidget
			# TODO: fix to allow choice of dock location
			self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
			self.dockwidget.show()
			
			#filtrage et peuplement des ComboBox des layers
			self.dockwidget.mMapLayerComboBox_IMPLUVIUM.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_SOL.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_EPIKARST.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_ROCHE.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_STRUCTURE.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_KARST_FEATURES.setFilters(QgsMapLayerProxyModel.VectorLayer)
			self.dockwidget.mMapLayerComboBox_ZNS.setFilters(QgsMapLayerProxyModel.RasterLayer)
			self.dockwidget.mMapLayerComboBox_PENTE.setFilters(QgsMapLayerProxyModel.RasterLayer)
			self.dockwidget.mMapLayerComboBox_CartePF.setFilters(QgsMapLayerProxyModel.RasterLayer)
			self.dockwidget.mMapLayerComboBox_CarteRF.setFilters(QgsMapLayerProxyModel.RasterLayer)
			self.dockwidget.mMapLayerComboBox_CarteIF.setFilters(QgsMapLayerProxyModel.RasterLayer)
			self.dockwidget.mMapLayerComboBox_CarteKaF.setFilters(QgsMapLayerProxyModel.RasterLayer)
			
			# peuplement de la comboBox du critere de Mangin
			self.dockwidget.comboBox_MANGIN.addItems(['1','2','3','4','5'])
		
			# peuplement des ComboBox des champs et gestion des criteres optionnels
				#SOL
			self.dockwidget.mFieldComboBox_SOL.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_SOL.setLayer(self.dockwidget.mMapLayerComboBox_SOL.currentLayer())
			self.dockwidget.mMapLayerComboBox_SOL.layerChanged.connect(self.dockwidget.mFieldComboBox_SOL.setLayer)
				#EPIKARST
			self.dockwidget.mFieldComboBox_EPIKARST.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_EPIKARST.setLayer(self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer())
			self.dockwidget.mMapLayerComboBox_EPIKARST.layerChanged.connect(self.dockwidget.mFieldComboBox_EPIKARST.setLayer)
			self.dockwidget.checkBox_Epikarst.stateChanged.connect(self.desactive_widget_Epikarst)
				#SINKING STREAM CATCHMENT
			self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setLayer(self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer())
			self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.layerChanged.connect(self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setLayer)
			self.dockwidget.checkBox_Sinking.stateChanged.connect(self.desactive_widget_Sinking)
				#LITHOLOGY
			self.dockwidget.mFieldComboBox_ROCHE.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_ROCHE.setLayer(self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer())
			self.dockwidget.mMapLayerComboBox_ROCHE.layerChanged.connect(self.dockwidget.mFieldComboBox_ROCHE.setLayer)
				#STRUCTURE
			self.dockwidget.mFieldComboBox_STRUCTURE.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_STRUCTURE.setLayer(self.dockwidget.mMapLayerComboBox_STRUCTURE.currentLayer())
			self.dockwidget.mMapLayerComboBox_STRUCTURE.layerChanged.connect(self.dockwidget.mFieldComboBox_STRUCTURE.setLayer)
			self.dockwidget.checkBox_STRUCTURE.stateChanged.connect(self.desactive_widget_structure)
				#KARST FEATURES I
			self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setLayer(self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer())
			self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.layerChanged.connect(self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setLayer)
			self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.stateChanged.connect(self.desactive_widget_objets_exokarstiques)
				#KARST FEATURES Ka
			self.dockwidget.mFieldComboBox_KARST_FEATURES.setFilters(QgsFieldProxyModel.Numeric)
			self.dockwidget.mFieldComboBox_KARST_FEATURES.setLayer(self.dockwidget.mMapLayerComboBox_KARST_FEATURES.currentLayer())
			self.dockwidget.mMapLayerComboBox_KARST_FEATURES.layerChanged.connect(self.dockwidget.mFieldComboBox_KARST_FEATURES.setLayer)
			self.dockwidget.checkBox_KARST_FEATURES.stateChanged.connect(self.desactive_widget_karst_features)
				
	
	def desactive_widget_Epikarst(self):
		if self.dockwidget.checkBox_Epikarst.isChecked():
			self.dockwidget.mMapLayerComboBox_EPIKARST.setEnabled(True)
			self.dockwidget.mFieldComboBox_EPIKARST.setEnabled(True)
			self.dockwidget.label_EPIKARST.setStyleSheet('color: black')
			self.dockwidget.label_index_EPIKARST.setStyleSheet('color: black')
		else:
			self.dockwidget.mMapLayerComboBox_EPIKARST.setDisabled(True)
			self.dockwidget.mFieldComboBox_EPIKARST.setDisabled(True)
			self.dockwidget.label_EPIKARST.setStyleSheet('color: grey')
			self.dockwidget.label_index_EPIKARST.setStyleSheet('color: grey')
			
	def desactive_widget_Sinking(self):
		if self.dockwidget.checkBox_Sinking.isChecked():
			self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.setEnabled(True)
			self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setEnabled(True)
			self.dockwidget.label_SINKING.setStyleSheet('color: black')
			self.dockwidget.label_index_SINKING.setStyleSheet('color: black')
		else:
			self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.setDisabled(True)
			self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.setDisabled(True)
			self.dockwidget.label_SINKING.setStyleSheet('color: grey')
			self.dockwidget.label_index_SINKING.setStyleSheet('color: grey')
	
	def desactive_widget_structure(self):
		if self.dockwidget.checkBox_STRUCTURE.isChecked():
			self.dockwidget.mMapLayerComboBox_STRUCTURE.setEnabled(True)
			self.dockwidget.mFieldComboBox_STRUCTURE.setEnabled(True)
			self.dockwidget.label_STRUCTURE.setStyleSheet('color: black')
			self.dockwidget.label_index_STRUCTURE.setStyleSheet('color: black')
		else:
			self.dockwidget.mMapLayerComboBox_STRUCTURE.setDisabled(True)
			self.dockwidget.mFieldComboBox_STRUCTURE.setDisabled(True)
			self.dockwidget.label_STRUCTURE.setStyleSheet('color: grey')
			self.dockwidget.label_index_STRUCTURE.setStyleSheet('color: grey')
		
	def desactive_widget_objets_exokarstiques(self):
		if self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
			self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setEnabled(True)
			self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setEnabled(True)
			self.dockwidget.label_OBJETS_EXOKARSTIQUES.setStyleSheet('color: black')
			self.dockwidget.label_index_OBJETS_EXOKARSTIQUES.setStyleSheet('color: black')
		else:
			self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.setDisabled(True)
			self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.setDisabled(True)
			self.dockwidget.label_OBJETS_EXOKARSTIQUES.setStyleSheet('color: grey')
			self.dockwidget.label_index_OBJETS_EXOKARSTIQUES.setStyleSheet('color: grey')
		
	def desactive_widget_karst_features(self):
		if self.dockwidget.checkBox_KARST_FEATURES.isChecked():
			self.dockwidget.mMapLayerComboBox_KARST_FEATURES.setEnabled(True)
			self.dockwidget.mFieldComboBox_KARST_FEATURES.setEnabled(True)
			self.dockwidget.label_KARST_FEATURES.setStyleSheet('color: black')
			self.dockwidget.label_index_KARST_FEATURES.setStyleSheet('color: black')
		else:
			self.dockwidget.mMapLayerComboBox_KARST_FEATURES.setDisabled(True)
			self.dockwidget.mFieldComboBox_KARST_FEATURES.setDisabled(True)
			self.dockwidget.label_KARST_FEATURES.setStyleSheet('color: grey')
			self.dockwidget.label_index_KARST_FEATURES.setStyleSheet('color: grey')
	
	########################################## FIN DE LA GESTION DE L'INTERFACE ########################################
	
	# fonction des push button 
	def open_directory(self):
		'''permet a l'utilisateur de choisir son repertoire de travail'''
		directory = QtGui.QFileDialog.getExistingDirectory(self.dockwidget.toolButton_dossier_travail,"Sélectionner le répertoire de travail", QgsProject.instance().fileName(), QtGui.QFileDialog.ShowDirsOnly)
		self.dockwidget.lineEdit_dossier_travail.setText(str(QtCore.QDir.toNativeSeparators(directory)))
	
	def lancer_genere_guide(self):
		'''lance la fonction de generation du guide''' 
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text())== False :
			return self.showdialog('Please check if the directory of generating is filled', 'Directory missing in the system...')
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Extension": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
		raster_extension.genere_guide(self.dockwidget.mMapLayerComboBox_IMPLUVIUM.currentLayer(), self.dockwidget.spinBox_Resolution.value(),self.dockwidget.lineEdit_dossier_travail.text() )
		self.iface.addRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/Extension.tif','Extension')		
	
	def lancer_carteP(self):
		'''test les parametres et lance la generation de la carte P'''
	# test pour ne pas lancer la fonction sans que la verification soit correcte
			#verifie que l'extension existe
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text() + '/Extension.tif')== False :
			 return self.showdialog('Please check if the directory of generating is filled and that the guide is already generate...', 'Layer Extension missing in the system...')
			
		#controle que la comboBox du champ SOL est bien remplie
		if self.dockwidget.mFieldComboBox_SOL.currentField() == u'':
			return self.showdialog('The index Field of Soil Protection Layer is not set...', 'Field issue...')
		#controle la validite des occurences du champ index
		value_sol = [feature.attribute(self.dockwidget.mFieldComboBox_SOL.currentField()) for feature in self.dockwidget.mMapLayerComboBox_SOL.currentLayer().getFeatures()]
		if min(value_sol) < 0 or max(value_sol) > 4 or len(value_sol) == 0 :
			return self.showdialog('The index Field of Soil Cover Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

		if self.dockwidget.checkBox_Epikarst.isChecked():
			#controle que la comboBox du champ Epikarst est bien remplie
			if self.dockwidget.mFieldComboBox_EPIKARST.currentField() == u'':
				return self.showdialog('The index Field of Epikarst Layer is not set...', 'Field issue...')
			#controle la validite des occurences du champ index
			value_epikarst = [feature.attribute(self.dockwidget.mFieldComboBox_EPIKARST.currentField()) for feature in self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer().getFeatures()]
			if min(value_epikarst) < 0 or max(value_epikarst) > 4 or len(value_epikarst) == 0 :
				return self.showdialog('The index Field of Epikarst Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

		if self.dockwidget.checkBox_Sinking.isChecked():
			#controle que la comboBox du champ Sinking Stream Catchment est bien remplie
			if self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField() == u'':
				return self.showdialog('The index Field of Sinking Stream Catchment Layer is not set...', 'Field issue...')
			#controle la validite des occurences des champs index
			value_sinking = [feature.attribute(self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField()) for feature in self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer().getFeatures()]
			if min(value_sinking) < 0 or max(value_sinking) > 4 or len(value_sinking) == 0 :
				return self.showdialog('The index''s field of Sinking catchment Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')
		
	################################ si les test sont satisfait, lance la fonction	
		#recupere l'extension
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Extension": 
				layer = QgsRasterLayer(lyr.source(),"extension")
			else :
				pass
				
		#genere les parametres a passer
			#SOL
		sol = self.dockwidget.mMapLayerComboBox_SOL.currentLayer()
		field_sol = self.dockwidget.mFieldComboBox_SOL.currentField()
			#EPIKARST
		if self.dockwidget.checkBox_Epikarst.isChecked():
			epikarst = self.dockwidget.mMapLayerComboBox_EPIKARST.currentLayer()
			field_epikarst = self.dockwidget.mFieldComboBox_EPIKARST.currentField()
		else :
			epikarst = None
			field_epikarst = None
			
			#SINKING CATCHMENT
		if self.dockwidget.checkBox_Sinking.isChecked():
			sinking = self.dockwidget.mMapLayerComboBox_SINKING_CATCHMENT.currentLayer()
			field_sinking = self.dockwidget.mFieldComboBox_SINKING_CATCHMENT.currentField()
		else : 
			sinking = None
			field_sinking = None 
		
		#lance la generation de la carte P
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "P factor": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
				
		Carte_P.genere_carteP(
			layer,
			self.dockwidget.lineEdit_dossier_travail.text(),
			self.dockwidget.mMapLayerComboBox_ZNS.currentLayer(),
			sol,
			field_sol,
			epikarst,
			field_epikarst,
			sinking,
			field_sinking)
			
		#genere le style et charge le tif dans QGIS avec un message
		lay_carteP = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/P_factor.tif','P factor')
		s = QgsRasterShader()
		c = QgsColorRampShader()
		c.setColorRampType(QgsColorRampShader.EXACT)
		i = []
		i.append(QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#FFFFFF'), '0'))
		i.append(QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#0040FF'), '1'))
		i.append(QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#A8D990'), '2'))
		i.append(QgsColorRampShader.ColorRampItem(3, QtGui.QColor('#F6F085'), '3'))
		i.append(QgsColorRampShader.ColorRampItem(4, QtGui.QColor('#E6A55B'), '4'))
		i.append(QgsColorRampShader.ColorRampItem(5, QtGui.QColor('#A43C27'), '5'))
		c.setColorRampItemList(i)
		s.setRasterShaderFunction(c)
		ps = QgsSingleBandPseudoColorRenderer(lay_carteP.dataProvider(), 1, s)
		lay_carteP.setRenderer(ps)
		QgsMapLayerRegistry.instance().addMapLayer(lay_carteP)
		self.showdialog('P factor map created wih success!', 'Well done!')
		
	def lancer_carteR(self):
		'''teste les parametres et lance la generation de la carte R'''
		
		############################# test pour ne pas lancer la fonction sans que la verification soit correcte
			#verifie que l'extension existe
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text() + '/Extension.tif')== False :
			return self.showdialog('Please check if the directory of generating is filled and that the guide is already generate...', 'Layer Extension missing in the system...')
			
				#LITHOLOGY
		#controle que la comboBox du champ est bien remplie
		if self.dockwidget.mFieldComboBox_ROCHE.currentField() == u'':
				return self.showdialog('The index Field of Lithology Layer is not set...', 'Field issue...')
		#controle la validite des occurences du champ index		
		value_lithology = [feature.attribute(self.dockwidget.mFieldComboBox_ROCHE.currentField()) for feature in self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer().getFeatures()]
		if min(value_lithology) < 0 or max(value_lithology) > 4 or len(value_lithology) == 0 :
			return self.showdialog('The index Field of Lithology Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')

				#STRUCTURE
		if self.dockwidget.checkBox_STRUCTURE.isChecked():
			#controle que la comboBox du champ Structure est bien remplie
			if self.dockwidget.mFieldComboBox_STRUCTURE.currentField() == u'':
				return self.showdialog('The index Field of Structure Layer is not set...', 'Field issue...')
			
			value_structure = [feature.attribute(self.dockwidget.mFieldComboBox_STRUCTURE.currentField()) for feature in self.dockwidget.mMapLayerComboBox_STRUCTURE.currentLayer().getFeatures()]
			if min(value_structure) < 0 or max(value_structure) > 4 or len(value_structure) == 0 :
				return self.showdialog('The index Field of Structure Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')


		
		################################ si les test sont satisfait, lance la fonction	
		#genere les parametres a passer
			#LITHOLOGY
		lithology = self.dockwidget.mMapLayerComboBox_ROCHE.currentLayer()
		field_lithology = self.dockwidget.mFieldComboBox_ROCHE.currentField()		
			#STRUCTURE
		if self.dockwidget.checkBox_STRUCTURE.isChecked():
			structure = self.dockwidget.mMapLayerComboBox_STRUCTURE.currentLayer()
			field_structure = self.dockwidget.mFieldComboBox_STRUCTURE.currentField()
		else:
			structure = None
			field_structure = None
		
		#lance la generation de la carte R
			#recupere l'extension
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Extension": 
				layer = QgsRasterLayer(lyr.source(),"extension")
			else :
				pass
		#lance la generation la carte R
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "R factor": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
				
		Carte_R.genere_carteR(
			self.dockwidget.lineEdit_dossier_travail.text(),
			layer,
			lithology,
			field_lithology,
			structure,
			field_structure)
		
		#genere le style et charge le tif dans QGIS
		lay_carteR = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/R_factor.tif','R factor')
		s = QgsRasterShader()
		c = QgsColorRampShader()
		c.setColorRampType(QgsColorRampShader.EXACT)
		i = []
		i.append(QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#FFFFFF'), '0'))
		i.append(QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#A8D990'), '1'))
		i.append(QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#F6F085'), '2'))
		i.append(QgsColorRampShader.ColorRampItem(3, QtGui.QColor('#E6A55B'), '3'))
		i.append(QgsColorRampShader.ColorRampItem(4, QtGui.QColor('#A43C27'), '4'))
		c.setColorRampItemList(i)
		s.setRasterShaderFunction(c)
		ps = QgsSingleBandPseudoColorRenderer(lay_carteR.dataProvider(), 1, s)
		lay_carteR.setRenderer(ps)
		QgsMapLayerRegistry.instance().addMapLayer(lay_carteR)
		self.showdialog('R factor map created wih success!', 'Well done!')
			
	def lancer_carteI(self):
		'''teste les parametres et lance la generation de la carte I'''
		########################## test pour ne pas lancer la fonction sans que la verification soit correcte
			#verifie que l'extension exist
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text() + '/Extension.tif')== False :
			return self.showdialog('Please check if the directory of generating is filled and that the guide is already generate...', 'Layer Extension missing in the system...')
			
				#OBJETS_EXOKARSTIQUES
		if self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
			#controle que la comboBox du champ est bien remplie
			if self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField() == u'':
				return self.showdialog('The index Field of Karst features Layer is not set...', 'Field issue...')
			#controle la validite des occurences des champs index
			value_objets_exokarstiques = [feature.attribute(self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField()) for feature in self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer().getFeatures()]
			if min(value_objets_exokarstiques) < 0 or max(value_objets_exokarstiques) > 4 :
				return self.showdialog('The index Field of Karst features Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')


		######################## Si les tests sont satisfait lance la fonction
			#genere les regles de reclassement selon les parametres donnes par l'utilisateur
		self.generate_reclass_rules_slope(self.dockwidget.spinBox_first_threshold.value(),self.dockwidget.spinBox_second_threshold.value(),self.dockwidget.spinBox_third_threshold.value())
			#recupere l'extension
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Extension": 
				layer = QgsRasterLayer(lyr.source(),"extension")
			else :
				pass
		#genere les parametres a passer
			#PENTE
		pente = self.dockwidget.mMapLayerComboBox_PENTE.currentLayer()
			#OBJETS_EXOKARSTIQUES
		if self.dockwidget.checkBox_OBJETS_EXOKARSTIQUES.isChecked():
			exokarst = self.dockwidget.mMapLayerComboBox_OBJETS_EXOKARSTIQUES.currentLayer()
			field_exokarst = self.dockwidget.mFieldComboBox_OBJETS_EXOKARSTIQUES.currentField()
		else:
			exokarst = None
			field_exokarst = None
		
		#lance la generation de la carte I
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "I Factor": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
				
		Carte_I.genere_carteI(
			self.dockwidget.lineEdit_dossier_travail.text(),
			layer,
			pente,
			os.path.dirname(os.path.abspath(__file__))+'/reclass_rules/reclass_rules_slope.txt',
			exokarst,
			field_exokarst)
			
		#genere le style et charge le tif dans QGIS
		lay_carteI = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/I_factor.tif','I factor')
		s = QgsRasterShader()
		c = QgsColorRampShader()
		c.setColorRampType(QgsColorRampShader.EXACT)
		i = []
		i.append(QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#FFFFFF'), '0'))
		i.append(QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#A8D990'), '1'))
		i.append(QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#F6F085'), '2'))
		i.append(QgsColorRampShader.ColorRampItem(3, QtGui.QColor('#E6A55B'), '3'))
		i.append(QgsColorRampShader.ColorRampItem(4, QtGui.QColor('#A43C27'), '4'))
		c.setColorRampItemList(i)
		s.setRasterShaderFunction(c)
		ps = QgsSingleBandPseudoColorRenderer(lay_carteI.dataProvider(), 1, s)
		lay_carteI.setRenderer(ps)
		QgsMapLayerRegistry.instance().addMapLayer(lay_carteI)
		self.showdialog('I factor map created wih success!', 'Well done!')
		
	def lancer_carteKa(self):
		'''teste les parametres et lance la generation de la carte Ka'''
		########################## test pour ne pas lancer la fonction sans que la verification soit correcte
			#verifie que l'extension exist
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text() + '/Extension.tif')== False :
			return self.showdialog('Please check if the directory of generating is filled and that the guide is already generate...', 'Layer Extension missing in the system...')
		
		if self.dockwidget.checkBox_KARST_FEATURES.isChecked():		
			#controle que la comboBox du champ est bien remplie
			if self.dockwidget.mFieldComboBox_KARST_FEATURES.currentField() == u'':
				return self.showdialog('The index Field of Karst features Layer is not set...', 'Field issue...')
			#controle la validite des occurences des champs index
				#KARST_FEATURES
			value_karst_features = [feature.attribute(self.dockwidget.mFieldComboBox_KARST_FEATURES.currentField()) for feature in self.dockwidget.mMapLayerComboBox_KARST_FEATURES.currentLayer().getFeatures()]
			if min(value_karst_features) < 0 or max(value_karst_features) > 4 or len(value_karst_features) == 0 :
				return self.showdialog('The index Field of Karst features Layer has wrong value... (not between 0 and 4 or null)', 'Index issue...')
		
		############################# Si les tests sont satisfait lance la fonction
		#recupere l'extension
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Extension": 
				layer = QgsRasterLayer(lyr.source(),"extension")
			else :
				pass
		#genere les parametre
		if self.dockwidget.checkBox_KARST_FEATURES.isChecked():
			karst_features = self.dockwidget.mMapLayerComboBox_KARST_FEATURES.currentLayer()
			field_karst_features = self.dockwidget.mFieldComboBox_KARST_FEATURES.currentField()
		else:
			karst_features = None
			field_karst_features = None
		
		#genere le tif
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Ka factor": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
		Carte_Ka.genere_carteKa(
			int(self.dockwidget.comboBox_MANGIN.currentText()),
			karst_features,
			field_karst_features,
			layer, 
			self.dockwidget.lineEdit_dossier_travail.text())
		#genere le style et charge le tif dans QGIS
		lay_carteKa = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/Ka_factor.tif','Ka factor')
		s = QgsRasterShader()
		c = QgsColorRampShader()
		c.setColorRampType(QgsColorRampShader.EXACT)
		i = []
		i.append(QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#FFFFFF'), '0'))
		i.append(QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#A8D990'), '1'))
		i.append(QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#F6F085'), '2'))
		i.append(QgsColorRampShader.ColorRampItem(3, QtGui.QColor('#E6A55B'), '3'))
		i.append(QgsColorRampShader.ColorRampItem(4, QtGui.QColor('#A43C27'), '4'))
		c.setColorRampItemList(i)
		s.setRasterShaderFunction(c)
		ps = QgsSingleBandPseudoColorRenderer(lay_carteKa.dataProvider(), 1, s)
		lay_carteKa.setRenderer(ps)
		QgsMapLayerRegistry.instance().addMapLayer(lay_carteKa)
		self.showdialog('Ka factor map created wih success!', 'Well done!')
	
	def lancer_carteFinale(self):
		'''fonction de generation, mise en forme et chargement de la carte finale'''
		if os.path.exists(self.dockwidget.lineEdit_dossier_travail.text())== False :
			return self.showdialog('Please check if the directory of generating is filled', 'Directory missing in the system...')
		#verifie la ponderation
		pP=self.dockwidget.spinBox_PondP.value()
		pR=self.dockwidget.spinBox_PondR.value()
		pI=self.dockwidget.spinBox_PondI.value()
		pKa=self.dockwidget.spinBox_PondKa.value()
		if pI + pKa < 50 :
			self.iface.messageBar().pushMessage('Anormal weight','I weight + Ka weight must be superior at 50%!', level=QgsMessageBar.WARNING, duration = 5)
		if pI + pKa > 65 :
			self.iface.messageBar().pushMessage('Anormal weight','I weight + Ka weight must be inferior at 65%!', level=QgsMessageBar.WARNING, duration = 5)
		if pP + pR < 35:
			self.iface.messageBar().pushMessage('Anormal weight','P weight + R weight must be superior at 35%!', level=QgsMessageBar.WARNING, duration = 5)
		if pP + pR > 50:
			self.iface.messageBar().pushMessage('Anormal weight','P weight + R weight must be inferior at 50%!', level=QgsMessageBar.WARNING, duration = 5)
		if pI + pKa + pP + pR != 100:
			return self.showdialog('weight sum must be egal at 100%!', 'invalid weight...')
			
		#supprime la couche si elle est deja chargee et genere le tif
		for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
			if lyr.name() == "Vulnerability Map": 
				QgsMapLayerRegistry.instance().removeMapLayers( [lyr.id()] )
				
		Carte_Finale.genere_carteFinale(self.dockwidget.spinBox_PondP.value(),self.dockwidget.spinBox_PondR.value(),self.dockwidget.spinBox_PondI.value(),self.dockwidget.spinBox_PondKa.value(),self.dockwidget.mMapLayerComboBox_CartePF.currentLayer(),self.dockwidget.mMapLayerComboBox_CarteRF.currentLayer(),self.dockwidget.mMapLayerComboBox_CarteIF.currentLayer(),self.dockwidget.mMapLayerComboBox_CarteKaF.currentLayer(),self.dockwidget.lineEdit_dossier_travail.text())
		#genere le style et charge le tif dans QGIS
		lay_carteFinale = QgsRasterLayer(str(self.dockwidget.lineEdit_dossier_travail.text())+'/Vulnerability_Map.tif','Vulnerability Map')
		s = QgsRasterShader()
		c = QgsColorRampShader()
		c.setColorRampType(QgsColorRampShader.EXACT)
		i = []
		i.append(QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#FFFFFF'), '0'))
		i.append(QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#A8D990'), '1'))
		i.append(QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#F6F085'), '2'))
		i.append(QgsColorRampShader.ColorRampItem(3, QtGui.QColor('#E6A55B'), '3'))
		i.append(QgsColorRampShader.ColorRampItem(4, QtGui.QColor('#A43C27'), '4'))
		c.setColorRampItemList(i)
		s.setRasterShaderFunction(c)
		ps = QgsSingleBandPseudoColorRenderer(lay_carteFinale.dataProvider(), 1, s)
		lay_carteFinale.setRenderer(ps)
		QgsMapLayerRegistry.instance().addMapLayer(lay_carteFinale)
		return self.showdialog('Final map created wih success!', 'Well done!')
	
	def showdialog (self, text, title):
		'''fonction permettant d'afficher des messages a l'utilisateur'''
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText(text)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()
	
	def open_Apropos(self):
		'''fonction d'ouverture de la fenetre A propos, connectee a son PushButton'''
		Dialog = QtGui.QDialog()
		md = Ui_A_propos()
		md.setupUi(Dialog)
		Dialog.exec_()
	
	def download_methodo(self):
		'''fonction d'ouverture de la methodologie officielle PaPRIKa'''
		webbrowser.open_new('http://infoterre.brgm.fr/rapports/RP-57527-FR.pdf')
		webbrowser.open_new_tab('http://link.springer.com/article/10.1007/s10040-010-0688-8')
	
	def open_help(self):
		'''fonction d'ouverture de la documentation du plugin'''
		os.startfile(os.path.dirname(os.path.abspath(__file__))+'/doc/Paprika_Toolbox_User_guide.pdf')
	
	def generate_reclass_rules_slope(self,first,second,third):
		'''fonction de generation du fichier .txt des regles de reclassement de la pente, le fichier est genere dans le repertoire du plugin'''
		reclass_rules = open(os.path.dirname(os.path.abspath(__file__))+'/reclass_rules/reclass_rules_slope.txt', 'w')
		reclass_rules.write('0 thru ' + str(first) + '= 4\n')
		reclass_rules.write(str(first) + ' thru ' + str(second) + '= 3\n')
		reclass_rules.write(str(second) + ' thru ' + str(third) + '= 2\n')
		reclass_rules.write(str(third) + ' thru 9999999' + '= 1')
		reclass_rules.close()
	
	def update_log(self, message):
		'''ajout des messages a l'utilisateur dans une fenetre de log'''
		#to do
