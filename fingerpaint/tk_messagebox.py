import tkinter


def message_box(title, message, button_text="Ok"):
    top = tkinter.Tk()
    top.title(title)

    icon = tkinter.Label(top, image="::tk::icons::error")
    icon.grid(row=0, column=0, padx=10, pady=10, sticky=tkinter.N)

    label = tkinter.Text(
        top,
        height=1 + message.count("\n"),
        width=max(len(line) for line in message.split("\n")),
        wrap=tkinter.WORD,
    )
    label.insert(1.0, message)
    label.grid(row=0, column=1, padx=10, pady=10, sticky=tkinter.N)

    label.configure(bg=top.cget("bg"), relief="flat")
    label.configure(state="disabled")

    # top.label = tkinter.Label(text=message)
    # top.label.grid(row=0, column=1, padx=10, pady=10, sticky=tkinter.N)

    def ok(event=None):
        top.destroy()

    ok_button = tkinter.Button(top, text=button_text, command=ok)
    ok_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky=tkinter.NE)

    top.mainloop()


if __name__ == "__main__":
    message_box(
        "Title",
        "Message Message Message\nMessage\nMessage Message Message AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
