# playlabs complete script

. /usr/share/bash-completion/completions/git

_playlabs_autocomplete()
{
	if [ "$playlabs_path" == '' ]
	then
		export playlabs_path=`pip3 show playlabs | grep "^Location" | awk '{print $2}'`
	fi

	local cur prev action=""
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"
	prevm="${COMP_WORDS[COMP_CWORD-2]}"

	local opts
	opts=('deploy' 'init' 'scaffold' 'install' 'git ' 'backup' 'restore' 'log')

	for i in ${opts[*]}
	do
		for j in ${COMP_WORDS[*]}; #=${COMP_WORDS}; $j >= 0; $j=$j + 1;
		do
			if [ $i == $j ]
				then action="${i}"
			fi
		done
	done


	case "${cur:0:1}" in
		@)
			local hosts
			[[ -f ${HOME}/.ssh/known_hosts ]] &&
				hosts=`cat ${HOME}/.ssh/known_hosts | awk '{print "@"$1}'`
			COMPREPLY=( $(compgen -W "${hosts}" -- ${cur} ) )
			return 0
		;;
	esac
	if [ "${action}" != "" ]
	then
		case "${action}" in
			scaffold)
				COMPREPLY=( $(compgen -d -- ${cur}) )
			;;
			install)
				local roles_path="${playlabs_path}/playlabs/roles"
				local running="`ls -l ${roles_path} | grep "^d" | awk '{print $9}'`"
				local last=`awk '{b=split($0,a,",");print(a[b]);}' <<< ${cur}`
				COMPREPLY=( $(compgen -W "${running}" -- "${last}") )
			;;
			deploy)
				COMPREPLY=( $(compgen -P 'image=' -A file -- ${cur}) )
			;;
			git)
				((COMP_CWORD -=1))
				COMP_WORDS=(${COMP_WORDS[@]:1})
				__git_func_wrap __git_main ;
				return 0
			;;
			*)
			;;
		esac
	else
		COMPREPLY=($(compgen -W "${opts[*]}" -- ${cur}))  
	fi

}

complete -F _playlabs_autocomplete playlabs
