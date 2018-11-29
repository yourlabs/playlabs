CLI Options
===========

Some of the variables you can like ::

    -e key=value                    # set variable "key" to "value"
    -e '{"key":"value"}'            # same in json
    -i path/to/inventory_script.ext # load any numbers of inventory variables
    -i 1.2.4.4,                     # add a host by ip to this play
    --limit 1.2.4.4,                # limit play execution to these hosts
    --user your-other-user          # specify a particular username
    --noroot                        # don't try becoming root automatically

Note : all ansible-playbook arguments should work.
