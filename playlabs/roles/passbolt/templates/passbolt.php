<?php
return [
    /**
     * DEFAULT APP CONFIGURATION
     *
     * All the information in this section must be provided in order for passbolt to work
     * This configuration overrides the CakePHP defaults locating in app.php
     * Do not edit app.php as it may break your upgrade process
     */
    'App' => [
        // A base URL to use for absolute links.
        // The url where the passbolt instance will be reachable to your end users.
        // This information is need to render images in emails for example
        'fullBaseUrl' => 'https://{{ passbolt_dns }}',
    ],

    // Database configuration.
    'Datasources' => [
        'default' => [
            'host' => 'passbolt-mysql',
            //'port' => 'non_standard_port_number',
            'username' => 'passbolt',
            'password' => '{{ passbolt_mysql_password }}',
            'database' => 'passbolt',
        ],
    ],

    // Email configuration.
    'EmailTransport' => [
        'default' => [
            'host' => '172.17.0.1',
            'port' => 25,
            'username' => 'passbolt@{{ fqdn }}',
            'password' => null,
            // Is this a secure connection? true if yes, null if no.
            'tls' => null,
            //'timeout' => 30,
            //'client' => null,
            //'url' => null,
        ],
    ],
    'Email' => [
        'default' => [
            // Defines the default name and email of the sender of the emails.
            'from' => ['passbolt@{{ fqdn }}' => 'Passbolt'],
            //'charset' => 'utf-8',
            //'headerCharset' => 'utf-8',
        ],
    ],

    /**
     * DEFAULT PASSBOLT CONFIGURATION
     *
     * This is the default configuration.
     * It enforces the use of ssl, and does not provide a default OpenPGP key.
     * If your objective is to try passbolt quickly for evaluation purpose, and security is not important
     * you can use the demo config example provided in the next section below.
     */
    'passbolt' => [
        // GPG Configuration.
        // The keyring must to be owned and accessible by the webserver user.
        // Example: www-data user on Debian
        'gpg' => [
            // Tell GPG where to find the keyring.
            // If putenv is set to false, gnupg will use the default path ~/.gnupg.
            // For example :
            // - Apache on Centos it would be in '/usr/share/httpd/.gnupg'
            // - Apache on Debian it would be in '/var/www/.gnupg'
            // - Nginx on Centos it would be in '/var/lib/nginx/.gnupg'
            // - etc.
            //'keyring' => getenv("HOME") . DS . '.gnupg',
            //
            // Replace GNUPGHOME with above value even if it is set.
            //'putenv' => false,

            // Main server key.
            'serverKey' => [
                // Server private key fingerprint.
                'fingerprint' => '{{ gpg_fingerprint }}',
                'public' => CONFIG . 'gpg' . DS . 'serverkey.asc',
                'private' => CONFIG . 'gpg' . DS . 'serverkey_private.asc',
            ],
        ],
    ],
];
