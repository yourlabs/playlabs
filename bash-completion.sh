# playlabs complete script

_playlabs_autocomplete()
{
	if [ "$playlabs_path" == '' ]
	then
		export playlabs_path=`pip show playlabs | grep "^Location" | awk '{print $2}'`
	fi

	local cur prev action=""
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"
	prevm="${COMP_WORDS[COMP_CWORD-2]}"

	local opts
	opts=('deploy' 'bootstrap' 'install' 'backup' 'restore' 'log')

	for i in ${opts[*]}
	do
		for j in ${COMP_WORDS[*]}; #=${COMP_WORDS}; $j >= 0; $j=$j + 1;
		do
			if [ $i == $j ]
				then action="${i}"
			fi
		done
	done

	if [ "${action}" != "" ]
	then
		case "${prev}" in
			install)
				local roles_path="${playlabs_path}/playlabs/roles"
				local running="`ls -l ${roles_path} | grep "^d" | awk '{print $9}'`"
				local last=`awk '{b=split($0,a,",");print(a[b]);}' <<< ${cur}`
				COMPREPLY=( $(compgen -W "${running}" -- "${last}") )
			;;
			deploy)
				COMPREPLY=( $(compgen -P 'image=' -A file -- ${cur}) )
			;;
			image)
				if [ $action == "deploy" ]
				then
					cur= $( sed -e 's/^=//' <<< $cur )
					COMPREPLY=( $(compgen -o plusdirs -f -- ${cur}) )
				fi
			;;
			*)
				case "${prevm}" in
					image)
						if [ "${prev}" == "=" ]
						then
							COMPREPLY=( $(compgen -o plusdirs -f -- ${cur}) )
						fi
					;;
					*)
					;;
				esac
			;;
		esac
	else
		COMPREPLY=($(compgen -W "${opts[*]}" -- ${cur}))  
	fi

	local LASTCHAR=' '
	if [ ${#COMPREPLY[@]} = 1 ]; then
		[ -d "$COMPREPLY" ] && LASTCHAR='/'
		COMPREPLY=$(printf %q%s "$COMPREPLY" "$LASTCHAR")
	else
		for ((i=0; i < ${#COMPREPLY[@]}; i++)); do
				[ -d "${COMPREPLY[$i]}" ] && COMPREPLY[$i]="${COMPREPLY[$i]}/"
		done
	fi
	return 0
}

complete -o nospace -F _playlabs_autocomplete playlabs
