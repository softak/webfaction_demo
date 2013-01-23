Feature: Issue 50
    Setting up a custom shop background.

    Scenario: I have a store and what to change a background color
        Just look at the clean store
        Given I whant to set a "#AAAAAA" color, and "repeated" image "s/img/no-avatar.jpg"
        Then I see in a store profile "background:#AAAAAA url(/media/store_desings/no-avatar"
        Then I whant to clear the background
        Then I see in a store profile nothing!
