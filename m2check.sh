#!/usr/bin/env bash

TOTAL_TESTS=0
TESTS_PASSED=0
TESTS_FAILED=0

log () {
	echo "[*] $1"
}

test () {
	echo "[?] $1"
	((TOTAL_TESTS++))
}

pass () {
	echo "[+] $1"
	((TESTS_PASSED++))
}

fail () {
	echo "[-] $1"
	((TESTS_FAILED++))
}

display_usage() { 
    cat <<EOM
    Usage: $(basename "$0") [create|check] path

    $(basename "$0") create /some/path
    
    	Run on the file server to create all necessary files and directories required for testing. 
    
    $(basename "$0") check /path/to/fuse/mountpoint

    	Run on the client.
EOM
} 

# if less than two arguments supplied, display usage 
if [ $# -le 1 ] 
then
	display_usage
	exit 1
fi 
 
if [[ ( $# == "--help") || $# == "-h" ]] 
then 
	display_usage
	exit 0
fi

if [[ $1 == "create" ]]
then
	BASEPATH=$2
	log "Attempting to create file layout..."
	test "Checking whether $BASEPATH exists..."
	# check to see if path exists
	if [[ -d "$BASEPATH" ]]
	then
		
		pass "$BASEPATH exists!"
		# check if it is empty (we don't want to clobber files)
		test "Checking whether $BASEPATH is empty..."
		if    ls -1qA "$2" | grep -q .
		then  
			fail "$BASEPATH is not empty. Please make sure the path contains no files."
			exit 1
		else  
			pass "$BASEPATH is empty. Creating file layout."
			log "admin"
			mkdir -p "$BASEPATH"/admin
			echo "this file is admin.txt" > "$BASEPATH"/admin/admin.txt
			log "config"
			mkdir -p "$BASEPATH"/config
			echo "this file is config.txt" > "$BASEPATH"/config/config.txt
			log "public"
			mkdir -p "$BASEPATH"/public
			echo "this file is public.txt" > "$BASEPATH"/public/public.txt
		fi
	else
		fail "$2 does not exist. Please specify a path that already exists on disk"
		exit 1
	fi
	log "Created file layout into $BASEPATH."
	exit 0

elif [[ $1 == "check" ]]
then
	BASEPATH=$2
	test "Checking whether $BASEPATH exists"
	if [[ -d "$BASEPATH" ]]
	then
		pass "$BASEPATH exists"
		# having fuse do the mount requires statfs 
		# ls on $BASEPATH uses access, getattr, readdir

		# check for nonexistent file. cat should return 1. requires getattr
		test "Checking for support of non-existent files"
		cat "$BASEPATH"/nonexistent/nonexistent.txt
		if [[ $? -eq 1 ]]
		then
			pass "Non-existent files check succeeded"
		else
			fail "Non-existent files check failed"
		fi

		array=( admin config public )
		for i in "${array[@]}"
		do
			test "Checking for readability of $i files"
			cat "$BASEPATH"/$i/$i.txt
		if [[ $? -eq 0 ]]
		then
			pass "$i/$i.txt read correctly"
		else
			fail "$i/$i.txt is not what we expected"
		fi	
		done
		
		# check if contents are what we expect 
		array=( admin config public )
		for i in "${array[@]}"
		do
			test "Checking if contents are correct for $i files"
			CONTENTS=$(cat "$BASEPATH"/$i/$i.txt)
		if [[ "$CONTENTS" == "this file is $i.txt" ]]
		then
			pass "$i/$i.txt has correct information"
		else
			fail "$i/$i.txt does not contain correct information $CONTENTS $i.txt"
		fi	
		done
		
		# check to see if we can create new empty files (no write call)
		test "Checking for ability to create new empty files"
		touch "$BASEPATH"/admin/newfile.txt
		if [[ $? -eq 0 ]]
		then
			pass "Successfully created an empty file (admin/newfile.txt)"
			
			rm "$BASEPATH"/admin/newfile.txt
		else
			fail "Unable to create a new file."
		fi

		# check to see if we can write stuff to files (write call)
		test "Checking to see if we can write a new file"
		echo "newcontents" > "$BASEPATH"/newfile.txt
		if [[ $? -eq 0 ]]
		then
			pass "Successfully added bytes to $BASEPATH/newfile.txt"
			
			rm "$BASEPATH"/newfile.txt
		else
			fail "Unable to create $BASEPATH/newfile.txt"
		fi

		test "Checking to see if we can update the access time of an existing file"
		FILE="$BASEPATH"/admin/admin.txt
		if [[ -f "$FILE" ]]; then
		    START=$(stat -c %Y "$FILE")
		    touch "$FILE"
		    END=$(stat -c %Y "$FILE")
		    if [[ $END -gt "$START" ]]
		    then
		    	pass "Successfully able to update access time of $FILE"
		    else
		    	fail "Unable to update access time of $FILE"
		    fi
		else 
		    echo "$FILE does not exist."
		fi

		test "Checking if we can delete a file"
		FILE="$BASEPATH"/admin/admin.txt
		if [[ -f "$FILE" ]]; then
		    CONTENTS=$(cat "$FILE")
		    rm "$FILE"
		    if [[ $? -eq 0 ]]
		    then
		    	pass "Successfilly able to delete $FILE"
		    	
		    	# rewriting contents into file 
		    	echo "$CONTENTS" > "$FILE"
		    else
		    	fail "Unable to delete $FILE"
		    fi
		else 
		    echo "$FILE does not exist."
		fi

		test "Checking to create a new directory"
		DIRECTORY="$BASEPATH"/newdir
		mkdir "$DIRECTORY"
		if [[ -d "$DIRECTORY" ]]
		then
			pass "Successfully able to create a new directory $DIRECTORY"
			
			#directory should be empty, removing
			rmdir "$DIRECTORY"
		else
			fail "Unable to create a new directory $DIRECTORY"
		fi
		
		test "Checking to see if we can chmod a file"
		FILE="$BASEPATH"/admin/admin.txt
		TEMP=$(stat -c %a "$FILE")
		chmod 777 "$FILE"
		if [[ $? -eq 0 ]]
		then
			pass "Successfully able to chmod $FILE"
			
			#undoing the change
			chmod "$TEMP" "$FILE"
		else
			fail "Unable to chmod $FILE $TEMP $CHMOD"
		fi
	else
		fail "$BASEPATH does not exist. Please specify a path that already exists on disk"
		exit 1
	fi
fi
echo ""
echo "<<< RESULTS >>>"
echo "Tests passed: $TESTS_PASSED/$TOTAL_TESTS"
echo "Tests failed: $TESTS_FAILED/$TOTAL_TESTS"
exit 0