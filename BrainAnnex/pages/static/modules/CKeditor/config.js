/* LAST MODIFIED 8/25/2016
 *
 * @license Copyright (c) 2003-2016, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

CKEDITOR.editorConfig = function( config ) {
	
	// %REMOVE_START%
	// The configuration options below are needed when running CKEditor from source files.
	config.plugins = 'dialogui,dialog,a11yhelp,basicstyles,blockquote,clipboard,panel,floatpanel,menu,contextmenu,resize,button,toolbar,elementspath,enterkey,entities,listblock,richcombo,format,horizontalrule,htmlwriter,wysiwygarea,image,indent,indentlist,fakeobjects,link,list,magicline,pastetext,pastefromword,removeformat,showborders,sourcearea,specialchar,menubutton,scayt,stylescombo,tab,table,tabletools,undo,wsc,panelbutton,autogrow,codeTag,colorbutton,colordialog,font,indentblock,smiley,symbol,justify,nbsp,pagebreak,showblocks,lineutils,widget,mathjax,image2,tableresize';
	config.skin = 'kama';
	// %REMOVE_END%

	// Define changes to default configuration here.
	// For complete reference see:
	// http://docs.ckeditor.com/#!/api/CKEDITOR.config

	// Any individual plugins added later on manually would go here:
	//config.extraPlugins = 'plugin1,plugin2,plugin3';	
	
	
	// Needed by "mathjax" plugin; contains URL of JavaScript to render TeX
	config.mathJaxLib = '//cdn.mathjax.org/mathjax/2.6-latest/MathJax.js?config=TeX-AMS_HTML';
	
	
	// The toolbar groups arrangement, optimized for two toolbar rows
	config.toolbar = [
		{ name: 'links', items: [ 'Link', 'Unlink', 'Anchor' ] },
		{ name: 'clipboard', items: [ 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo' ] },
		{ name: 'editing', items: [ 'Scayt' ] },
		{ name: 'insert', items: [ 'Image', 'Mathjax', 'Table', 'HorizontalRule', 'SpecialChar', 'Smiley', 'PageBreak', 'Code', 'Symbol' ] },
		{ name: 'tools', items: [ 'ShowBlocks' ] },
		{ name: 'document', items: [ 'Source' ] },
		'/',
		{ name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat' ] },
		{ name: 'paragraph', items: [ 'NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock' ] },
		{ name: 'styles', items: [ 'Styles', 'Font', 'FontSize' ] },
		{ name: 'colors', items: [ 'TextColor', 'BGColor' ] }
	];




	// Remove some buttons provided by the standard plugins, which are
	// I eliminated the "Format" pulldown menu because all I need is covered by the "Styles" pulldown menu
	config.removeButtons = 'Format,Paste,Copy,Cut';

	// Set the most common block elements.
	config.format_tags = 'p;h1;h2;h3;pre';

	// Simplify the dialog windows.
	config.removeDialogTabs = 'image:advanced;link:advanced';
	
	
	// Auto-grow parameters: see http://docs.ckeditor.com/#!/guide/dev_autogrow
	config.autoGrow_minHeight = 250;
	config.autoGrow_maxHeight = 400;
	config.autoGrow_onStartup = true;
	
	// The following line could be used in the absence of Auto-grow:
	// config.height = 400;
	
	
	config.toolbarCanCollapse = true;
};
