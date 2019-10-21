@ECHO OFF

REM Path variables
set qgis_user_dir=%UserProfile%\.qgis2
set rcl_plugin_dir=%qgis_user_dir%\python\plugins\esstoolkit

REM Make sure QGIS is installed
IF NOT EXIST %qgis_user_dir% (
	ECHO ERROR: QGIS not found.
	GOTO FAILURE
)

REM Remove potential previously installed plugin
IF EXIST "%rcl_plugin_dir%" (
	ECHO Removing currently installed Space Syntax Toolkit QGIS plugin...
	rmdir "%rcl_plugin_dir%" /s /q
	IF EXIST "%rcl_plugin_dir%" (
		ECHO ERROR: Couldn't remove currently installed Space Syntax Toolkit QGIS plugin.
		ECHO Please close QGIS if it is running, and then try installing again.
		GOTO FAILURE
	)
)

ECHO Copying Space Syntax Toolkit QGIS plugin to QGIS plugin directory...
xcopy "%~dp0*.*" "%rcl_plugin_dir%\" /syq
REM NOTE: The test below tests errorlevel >= 1, not errorlevel == 1
IF ERRORLEVEL 1 (
	ECHO ERROR: Couldn't copy files "%~dp0*.*" to "%rcl_plugin_dir%\"
	GOTO FAILURE
)

ECHO.
ECHO Space Syntax Toolkit QGIS plugin was successfully installed!
ECHO Please see readme.txt for instructions on how to enable it.
ECHO.
PAUSE
EXIT

:FAILURE
ECHO Space Syntax Toolkit QGIS plugin was NOT installed.
ECHO.
PAUSE