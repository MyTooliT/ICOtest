.. _configuration:

*************
Configuration
*************

Configuration values are stored in `YAML <https://yaml.org>`__ files handled by the configuration library `Dynaconf`_. The `default values`_ are stored inside the package itself. If you want to overwrite or extend these values you should create a user configuration file. To do that use the command:

.. code-block:: shell

   icotest config

which will open the the user configuration in your default text editor. You can then edit this file and save your changes to update the configuration. For a list of available options, please take a look at the `default configuration <default values_>`__. Please make sure to not make any mistakes when you edit this file. Otherwise (some of the tests) will not work, printing an error message about the (first) incorrect configuration value.

.. _Dynaconf: https://www.dynaconf.com
.. _default values: https://github.com/MyTooliT/ICOtest/blob/main/icotest/config/config.yaml

.. _simplicity:

Simplicity Commander
====================

For some of the tests you need to **either** install

- `Simplicity
  Studio <https://www.silabs.com/products/development-tools/software/simplicity-studio>`__
  or
- `Simplicity
  Commander <https://www.silabs.com/developers/mcu-programming-options>`__.

If you choose the first option, then please make sure to install the Simplicity Commander tool inside Simplicity Studio.

Linux
-----

Please add the path to ``commander`` to the list ``commands`` → ``path``
→ ``linux`` in the :ref:`configuration`.

macOS
-----

If you install Simplicity Studio or Simplicity Commander in the standard install path (``/Applications``) you do not need to change the config. If you put the application in a different directory, then please add the path to ``commander`` to the list ``commands`` → ``path`` → ``mac`` in the :ref:`configuration`.

Windows
-------

- If you installed Simplicity Studio (including Simplicity Studio) to the standard location, then you do not need to change the configuration.

- If you download Simplicity Commander directly, then the tests assume that you unzipped the files into the directory ``C:\SiliconLabs\Simplicity Commander`` or ``C:\Program Files\Simplicity Commander``.

- If you did not use any of the standard install path, then please add the path to ``commander.exe`` to the list ``commands`` → ``path`` → ``windows`` in the :ref:`configuration`.

..

   **Notes:**

   - You also need to install `J-Link <https://www.segger.com/downloads/jlink/>`__ for Simplicity Commander to work with a USB programmer.

   - If your device does not show up in Simplicity Commander and only appears as **USB BULK device in the Windows device manager**, then please `follow the steps described in the Segger Knowledge Base <https://kb.segger.com/J-Link_shown_as_generic_BULK_device_in_Windows>`__.

Additional Information
----------------------

If you **do not want to change the config**, and Simplicity Commander (``commander``) is not part of the standard search locations for your operating system, then please make sure that ``commander`` is accessible via the ``PATH`` environment variable.
