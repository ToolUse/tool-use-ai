from scriptomatic import Scriptomatic



def main(args=None):
    # Default values
    model = "gpt-4o"
    script_text = "Create a script that builds scripts"
    temperature = 0.7

    if args and len(args) >= 2:
        model = args[0]
        script_text = args[1]
        if len(args) >= 3:
            temperature = float(args[2])

    scriptomatic = Scriptomatic(model=model, temperature=temperature)
    scriptomatic.generate_script(script_text)


if __name__ == '__main__':
    main()
